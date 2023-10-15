from sqlalchemy.orm import Session
import model, schema

from datetime import datetime, date

def get_user(db: Session, user_id: int):
  return db.query(model.User).filter(model.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
  return db.query(model.User).filter(model.User.email == email).first()

def create_user(db: Session, user: schema.UserCreate):
  hashed_password = user.password
  db_user = model.User(email=user.email, password = user.password)
  db.add(db_user)
  db.commit()
  db.refresh(db_user)

  return db_user

def get_task(db: Session, task_id: int):
  return db.query(model.Task).filter(model.Task.id == task_id).first()

def get_task_by_owner_id(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
  return db.query(model.Task).filter(model.Task.owner_id == owner_id).offset(skip).limit(limit).all()

def get_task_by_date(db: Session, date: str):
  return db.query(model.Task).filter(model.Task.created_date == date).all()

def create_task(db: Session, task: schema.TaskCreate, user_id: int):
  db_task = model.Task(**task.model_dump(), owner_id = user_id, created_time = datetime.now(), created_date = date.today())
  db.add(db_task)
  db.commit()
  db.refresh(db_task)

  return db_task

def mark_task_complete(db: Session, task: model.Task):
  task.status = 1
  db.commit()
  db.refresh(task)

  return task

def delete_task(db: Session, task: model.Task):
  db.delete(task)
  db.commit()

