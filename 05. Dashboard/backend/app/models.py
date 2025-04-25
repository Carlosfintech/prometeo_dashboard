from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Modelos basados en la base de datos existente
class Client(Base):
    __tablename__ = "demographics"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    income = Column(Float, nullable=False)
    profile = Column(String, nullable=False)

class Prediction(Base):
    __tablename__ = "prediction_results"
    
    user_id = Column(Integer, ForeignKey("demographics.id"), primary_key=True)
    probability = Column(Float, nullable=False)
    pred_bin = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client")

class Contact(Base):
    __tablename__ = "contact_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("demographics.id"))
    status = Column(String, nullable=False)
    
    client = relationship("Client")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(String, nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("demographics.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client")
    product = relationship("Product")

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    target = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    period = Column(String, nullable=False)

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    probabilidad = Column(Float, nullable=False)
    estado = Column(String, nullable=False)
    edad = Column(Integer, nullable=False)
    ingreso = Column(String, nullable=False)
    perfil = Column(String, nullable=False)
    prioridad = Column(String, nullable=False)
    
    productos = relationship("ClienteProducto", back_populates="cliente")

class ClienteProducto(Base):
    __tablename__ = "cliente_productos"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(String, ForeignKey("clientes.id"))
    producto_id = Column(String, ForeignKey("productos.id"))
    
    cliente = relationship("Cliente", back_populates="productos")
    producto = relationship("Producto") 