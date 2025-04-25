from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

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

class Producto(Base):
    __tablename__ = "productos"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    tipo = Column(String, nullable=False)

class ClienteProducto(Base):
    __tablename__ = "cliente_productos"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(String, ForeignKey("clientes.id"))
    producto_id = Column(String, ForeignKey("productos.id"))
    
    cliente = relationship("Cliente", back_populates="productos")
    producto = relationship("Producto") 