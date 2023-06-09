import sys
sys.path.append('..')

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
import models
from sqlalchemy.orm import Session
from database import SessionLocal,engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime,timedelta
from jose import jwt,JWTError


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

class CreateUser(BaseModel):
    username : str
    email : Optional[str]
    first_name : str
    last_name : str
    password : str

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)

Oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')

router = APIRouter(
    prefix= '/auth',
    tags = ['auth'],
    responses={401:{'description': ' Not Found'}}
)

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

def create_access_token(username: str, user_id: int, expire_delta: Optional[timedelta] = None):
    encode = {'sub': username,'id':user_id}
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(Oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise get_user_exception()
        return {'username':username,'id': user_id}
    except JWTError:
        raise get_user_exception()


@router.post('/create/user')
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

@router.post('/token')
async def login_with_access_token(from_data: OAuth2PasswordRequestForm = Depends() , db: Session = Depends(get_db)):
    user = authenticate_user(from_data.username,from_data.password, db)
    if not user:
        return token_exception()
    token_expires = timedelta(minutes=15)
    token = create_access_token(user.username, user.id, expire_delta=token_expires)

    return {'token': token}

def success_response(status_code:int):
    return {
        'status':status_code ,
        'transaction': 'Successfully'
    }


#Exception
def get_user_exception():
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail='Could not valid credential',
        headers={'WWW-Authenticate':'Barear'}
    )
    return credentials_exception

def token_exception():
    token_exception_response = HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail='Could not find username and password',
        headers={'WWW-Authenticate':'Barear'}
        )

