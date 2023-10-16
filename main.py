from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

# For working with DB
from typing import List

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

import model, schema, crud
from database import SessionLocal, engine

from datetime import date

model.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

app = FastAPI()

# Sort DB Dependency
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def home(request: Request):
  return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def home(request: Request):
  return templates.TemplateResponse("register.html", {"request": request})

@app.get("/manage-task", response_class=HTMLResponse)
def home(request: Request):
  return templates.TemplateResponse("manage-task.html", {"request": request})

@app.post("/user", response_model=schema.User)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):
  db_user = crud.get_user_by_email(db, user.email)

  if db_user:
    raise HTTPException(status_code=404, detail="User already exist")

  return crud.create_user(db, user)

@app.post("/user/{user_id}/task/", response_model=schema.Task)
def create_task(user_id: int, task: schema.TaskCreate, db: Session = Depends(get_db)):
  db_user = crud.get_user(db, user_id)

  if not db_user:
    raise HTTPException(status_code=404, detail="User not found")

  return crud.create_task(db, task, user_id)

@app.post("/task/{task_id}/complete", response_model=schema.Task)
def complete_task(task_id: int, db: Session = Depends(get_db)):
  db_task = crud.get_task(db, task_id)

  if not db_task:
    raise HTTPException(status_code=404, detail="Task not found")

  return crud.mark_task_complete(db, db_task)

@app.post("/task/{task_id}/delete")
def delete_task(task_id: int, db: Session = Depends(get_db)):
  db_task = crud.get_task(db, task_id)

  if not db_task:
    raise HTTPException(status_code=404, detail="Task not found")

  crud.delete_task(db, db_task)

  return {'message': 'Task deleted successfuly'}

@app.get("/task/{user_id}/")
def get_task(user_id: int, db: Session = Depends(get_db)):
  db_task = crud.get_task_by_date(db, date.today(), user_id)

  if len(db_task) == 0:
    raise HTTPException(status_code=404, detail="No task found")

  return db_task


