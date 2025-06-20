from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.backend.db import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    comment = Column(String)
    comment_date = Column(DateTime, default=datetime.now())
    grade = Column(Float)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="reviews", uselist=False)