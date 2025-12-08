from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # admin, user
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sites = relationship("Site", back_populates="owner")

class Site(Base):
    __tablename__ = "sites"

    id = Column(String, primary_key=True, default=generate_uuid)
    slug = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    domain = Column(String, nullable=True) # Custom domain
    
    # owner_id = Column(String, ForeignKey("users.id"))
    # For simplicity in MVP if auth is optional or simple, we might skip owner constraint initially,
    # but let's include it for "production ready" goal.
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    visibility = Column(String, default="public") # public, password, ip_whitelist, token
    
    # Access Control Content
    password_hash = Column(String, nullable=True) # For site-level password
    ip_whitelist = Column(JSON, nullable=True) # List of IPs
    token = Column(String, nullable=True) # For token gating
    
    status = Column(String, default="pending") # pending, deploying, deployed, failed
    
    deployment_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="sites")
