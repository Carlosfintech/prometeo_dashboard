"""
Configuración y modelos de base de datos utilizando SQLAlchemy 2.0 async
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.future import select

# URL de la base de datos desde variables de entorno
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:1111@localhost:5432/prometeo_db")

# Crear motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base declarativa para los modelos
Base = declarative_base()

# Modelos
class Client(Base):
    __tablename__ = "demographics"  # Nombre real en la base de datos
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, nullable=False, index=True)
    age = Column(Integer)
    income_range = Column(String)
    risk_profile = Column(String)
    occupation = Column(String)
    profile_category = Column(String)
    segment = Column(String)
    acquisition_date = Column(DateTime)
    last_contact_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    probability = Column(Float, default=0.5)
    
    # Relaciones
    predictions = relationship("Prediction", back_populates="client", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client(id={self.id}, user_id='{self.user_id}', probability={self.probability:.2f})>"

class Prediction(Base):
    __tablename__ = "prediction_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("demographics.user_id"))
    probability = Column(Float)
    is_target = Column(Boolean)
    features = Column(String, nullable=True)
    prediction_date = Column(DateTime, nullable=True)
    actual_conversion = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True)
    
    # Relaciones
    client = relationship("Client", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, user_id='{self.user_id}', probability={self.probability:.2f})>"

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("demographics.id"))
    contacted_at = Column(DateTime, default=datetime.now)
    channel = Column(String)
    notes = Column(String, nullable=True)
    outcome = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relaciones
    client = relationship("Client", back_populates="contacts")
    
    def __repr__(self):
        return f"<Contact(id={self.id}, client_id={self.client_id}, channel='{self.channel}')>"

# Función para obtener una sesión de base de datos
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()