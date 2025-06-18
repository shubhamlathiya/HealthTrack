from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from utils.config import db


class OperationCategory(db.Model):
    """Model for operation categories"""
    __tablename__ = 'operation_categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to operations
    operations = relationship("Operation", back_populates="category")

    def __repr__(self):
        return f"<OperationCategory(id={self.id}, name='{self.name}')>"


class Operation(db.Model):
    """Model for medical operations/procedures"""
    __tablename__ = 'operations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    category_id = Column(Integer, ForeignKey('operation_categories.id'), nullable=True)
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to category
    category = relationship("OperationCategory", back_populates="operations")

    def __repr__(self):
        return f"<Operation(id={self.id}, name='{self.name}', category_id={self.category_id})>"
