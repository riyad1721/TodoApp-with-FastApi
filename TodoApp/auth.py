from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import models
from sqlalchemy.orm import Session
from database import SessionLocal,engine
from fastapi.security import OAuth2PasswordRequestForm

class CreateUser(BaseModel):
    username : str
    email : Optional[str]
    first_name : str
    last_name : str
    password : str

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return bcrypt_context.hash(password)

def varify_password(plain_password, hash_password):
    return bcrypt_context.verify(plain_password, hash_password)

def authenticate_user(username: str, password : str, db):
    user = db.query(models.Users).filter(models.Users.username == username).first()

    if not user:
        return False
    if not varify_password(password, user.hashed_password):
        return False
    return user

@app.post('/create/user')
async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
    create_user_model = models.Users()
    create_user_model.email = create_user.email
    create_user_model.username = create_user.username
    create_user_model.first_name = create_user.first_name
    create_user_model.last_name = create_user.last_name
    hash_password = get_password_hash(create_user.password)
    create_user_model.hashed_password = hash_password
    create_user_model.is_active = True

    db.add(create_user_model)
    db.commit()

    return success_response(201)

@app.post('/token')
async def login_with_access_token(from_data: OAuth2PasswordRequestForm = Depends() , db: Session = Depends(get_db)):
    user = authenticate_user(from_data.username,from_data.password, db)
    if not user:
        return HTTPException(status_code=404,detail='Not found')
    return 'User Validated'

def success_response(status_code:int):
    return {
        'status':status_code ,
        'transaction': 'Successfully'
    }
