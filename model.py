from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime
from datetime import datetime

from database import Base

class User(Base):
  __tablename__ = "user"

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True)
  password = Column(String)

  tasks = relationship("Task", back_populates="owner")

class Task(Base):
  __tablename__ = "task"

  id = Column(Integer, primary_key=True, index=True)
  created_time = Column(DateTime)
  created_date = Column(Date)
  title = Column(String, nullable=False)
  status = Column(Boolean, default=False)
  owner_id = Column(Integer, ForeignKey("user.id"))

  owner = relationship("User", back_populates="tasks")
