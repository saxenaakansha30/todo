from typing import List
from pydantic import BaseModel
from datetime import date, datetime

class TaskBase(BaseModel):
  title: str
  status: bool = False

class TaskCreate(TaskBase):
  pass

class Task(TaskBase):
  id: int
  owner_id: int
  created_time: datetime
  created_date: date

  class Config:
    from_attributes = True

class UserBase(BaseModel):
  email: str

class UserCreate(UserBase):
  password: str

class User(UserBase):
  id: int
  tasks: List[Task] = []

  class Config:
    from_attributes = True

