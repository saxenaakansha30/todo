from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from datetime import date
from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import model, schema, crud
from database import SessionLocal, engine

# For login/logout functionality.
from dotenv import load_dotenv
import os
from fastapi_login import LoginManager
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status
from starlette.status import HTTP_400_BAD_REQUEST
from datetime import timedelta
from fastapi import Form

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = 30

manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# Sort DB Dependency
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

app.mount("/static", StaticFiles(directory="static"), name="static")
model.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

def get_hashed_password(plain_password):
  return pwd_ctx.hash(plain_password)

def verify_password(plain_password, hashed_password):
  return pwd_ctx.verify(plain_password, hashed_password)

@manager.user_loader()
def get_user(email: str, db: Session = Depends(get_db)):
  return crud.get_user_by_email(db, email)

def authenticate_user(email: str, password: str, db: Session = Depends(get_db)):
  user = crud.get_user_by_email(db, email)

  if not user:
    return None
  if not verify_password(password, user.password):
    return None

  return user


class NotAuthenticatedException(Exception):
  pass

def not_authenticated_exception_handler(request, exception):
  return RedirectResponse("/login")

manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(NotAuthenticatedException, not_authenticated_exception_handler)

#
# Build the API's #
#

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
  return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
  request: Request,
  form_data: OAuth2PasswordRequestForm = Depends(),
  db: Session = Depends(get_db)
  ):
  user = authenticate_user(form_data.username, form_data.password, db)

  if not user:
    return templates.TemplateResponse("/login.html", {"request": request, "invalid": True}, status_code=status.HTTP_401_UNAUTHORIZED)

  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = manager.create_access_token(
    data = {'sub': user.email},
    expires = access_token_expires
  )

  respone = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
  manager.set_cookie(respone, access_token)

  return respone

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
  return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
  request: Request,
  email: str = Form(...),
  password: str = Form(...),
  db: Session = Depends(get_db)
):
  user = crud.get_user_by_email(db, email)

  if user:
    return templates.TemplateResponse("/register.html", {"request": request, "invalid": True}, status_code=status.HTTP_401_UNAUTHORIZED)

  user = crud.create_user(db, schema.UserCreate(email=email, password=get_hashed_password(password)))

  return templates.TemplateResponse("/login.html", {"request": request}, status_code=status.HTTP_302_FOUND)

@app.get("/progress/{user_id}")
def get_progress(request: Request, user_id: int, db: Session = Depends(get_db)):
  user = crud.get_user(db, user_id)

  tasks = crud.get_task_by_date(db, date.today(), user_id)
  completed_task = crud.get_completed_task_by_owner_id(db, date.today(), user_id)
  progress = (len(completed_task) / len(tasks)) * 100

  return templates.TemplateResponse("progress.html", {"request": request, "tasks": tasks, "progress": progress, "user_id": user_id})


@app.get("/manage-task/{user_id}", response_class=HTMLResponse)
def get_tasks(request: Request, user_id: int, db: Session = Depends(get_db)):
  user = crud.get_user(db, user_id)

  tasks = crud.get_pending_task_by_owner_id(db, date.today(), user_id)

  return templates.TemplateResponse("manage-task.html", {"request": request, "tasks": tasks, "user_id": user_id})

@app.post("/user", response_model=schema.User)
def create_user(user: schema.UserCreate, db: Session = Depends(get_db)):
  db_user = crud.get_user_by_email(db, user.email)

  if db_user:
    raise HTTPException(status_code=404, detail="User already exist")

  return crud.create_user(db, user)

@app.post("/user/{user_id}/task/")
def create_task(
  user_id: int,
  title: str = Form(...),
  db: Session = Depends(get_db)):
  db_user = crud.get_user(db, user_id)

  if not db_user:
    return RedirectResponse("/404.html", status_code=status.HTTP_404_NOT_FOUND)
  task = schema.TaskCreate(title=title)
  crud.create_task(db, task, user_id)

  return RedirectResponse("/manage-task/1", status_code=status.HTTP_302_FOUND)


@app.post("/task/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
  db_task = crud.get_task(db, task_id)

  if not db_task:
    return RedirectResponse("/404.html", status_code=status.HTTP_302_FOUND)

  crud.mark_task_complete(db, db_task)

  return RedirectResponse("/manage-task/1", status_code=status.HTTP_302_FOUND)


@app.post("/task/{task_id}/delete")
def delete_task(
  task_id: int, db: Session = Depends(get_db)):
  db_task = crud.get_task(db, task_id)

  if not db_task:
    return RedirectResponse("/404.html", status_code=status.HTTP_302_FOUND)

  crud.delete_task(db, db_task)

  return RedirectResponse("/manage-task/1", status_code=status.HTTP_302_FOUND)

@app.get("/404", response_class=HTMLResponse)
def search(request: Request):
  return templates.TemplateResponse("404.html", {"request": request})
