"""
FastAPI + dependencias + endpoints necesarios para el dashboard.
"""
from typing import List
from fastapi import FastAPI, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import SessionLocal, Client, Prediction, Contact
from .schemas  import ClientOut, StatusIn, KPISummary

app = FastAPI(title="Prometeo API v1")

# CORS para frontend Vite/React (ajusta origenes en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_db():
    async with SessionLocal() as session:
        yield session


# ---------- KPIs ----------
@app.get("/api/v1/metrics/summary", response_model=KPISummary)
async def metrics_summary(db: AsyncSession = Depends(get_db)):
    threshold = 0.2389
    total_pot = await db.scalar(
        select(func.count()).select_from(Prediction).where(
            Prediction.probability >= threshold
        )
    )
    mean_conv = await db.scalar(select(func.avg(Prediction.probability)))
    return KPISummary(
        clientes_potenciales=total_pot or 0,
        conversion_esperada=round(mean_conv or 0, 4),
    )


# ---------- Tabla de clientes ----------
@app.get("/api/v1/clients/priority-list", response_model=List[ClientOut])
async def priority_list(
    page: int = Query(1, ge=1),
    size: int = Query(15, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Client, Prediction, Contact.status)
        .join(Prediction, Client.id == Prediction.user_id)
        .join(Contact, Contact.user_id == Client.id, isouter=True)
        .order_by(Prediction.probability.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.execute(stmt)).all()
    return [
        ClientOut(
            id=c.id,
            name=c.name,
            probability=p.probability,
            status=s,
            age=c.age,
            income=c.income,
            profile=c.profile,
        )
        for c, p, s in rows
    ]


# ---------- Actualizar estado ----------
@app.patch("/api/v1/clients/{user_id}/status")
async def update_status(
    user_id: int,
    body: StatusIn,
    db: AsyncSession = Depends(get_db),
):
    contact = await db.scalar(select(Contact).where(Contact.user_id == user_id))
    if not contact:
        contact = Contact(user_id=user_id, status=body.new_status)
        db.add(contact)
    else:
        contact.status = body.new_status
    await db.commit()
    return {"ok": True, "status": body.new_status}