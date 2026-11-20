import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True)
    brand = Column(String(100), index=True)
    title = Column(String(500), index=True)
    category = Column(String(100), default="General")
    search_query = Column(String(500))
    thumbnail_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_checked_at = Column(DateTime, default=datetime.datetime.utcnow)

    price_history = relationship("PricePointModel", back_populates="product", cascade="all, delete-orphan")

class PricePointModel(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    store_name = Column(String(50))
    price = Column(Float)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("ProductModel", back_populates="price_history")
