from database import SessionLocal
from datetime import timedelta, datetime, timezone
from fastapi import FastAPI,APIRouter,Depends,HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from models import Users
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated,Optional
from jose import jwt


route = APIRouter()

bcrypt_context = CryptContext(schemes= ['bcrypt'], deprecated = 'auto')
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl= 'login')

class CreateUser(BaseModel):
    email : str
    username: str
    fastname: str
    lastname: str
    password: str
    role : str 

class UpdateUser(BaseModel):
    email : Optional[str] =Field (default= None)
    username: Optional[str] =Field (default= None)
    fastname: Optional[str] =Field (default= None)
    lastname: Optional[str] =Field (default= None)
    role : Optional[str] =Field (default= None)

class UpdatePassword(BaseModel):
    current_password : str
    new_password : str

SCERET_KEY = '5bb7def1ea99e60cba3ae25ca6fb31d701091d833b9d5b7bdd0c14c9e591cfc4'
ALGORITHM = 'HS256'

def authenticate_user(username,password,db):
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        return False
    if bcrypt_context.verify(password,user.hash_password):
        return user
    return False

def create_access_token(username: str, user_id: str, role:str, expires_delta = timedelta):
    encode = {
        'sub' : username,
        'id' : user_id,
        'role' : role
    }
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp':expire})
    return jwt.encode(encode, SCERET_KEY, algorithm= ALGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        pyload = jwt.decode(token, SCERET_KEY, algorithms= ALGORITHM)
        username: str = pyload.get('sub')
        user_id : str = pyload.get('id')
        role : str = pyload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code= 404, detail= 'User Not Found.')
        return {'username' : username, 'id' : user_id, 'role' : role}
    except:
        raise HTTPException(status_code= 404, detail= 'User Not Found.')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependancey = Annotated[Session,Depends(get_db)]
user_dependancey = Annotated[dict, Depends(get_current_user)]
@route.post('/creatuser')
def create_user(db : db_dependancey, new_user: CreateUser):
    user_model = Users(
        email = new_user.email,
        username = new_user.username,
        fastname= new_user.fastname,
        lastname = new_user.lastname,
        hash_password = bcrypt_context.hash(new_user.password),
        is_active = True,
        role = new_user.role
    ) 
    db.add(user_model)
    db.commit()

    return JSONResponse(status_code= 201, content= {'Message' : 'User Created Sucessfully.'})



@route.post('/login')
def login_user(db: db_dependancey, from_data: Annotated[OAuth2PasswordRequestForm,Depends()]):
    user = authenticate_user(from_data.username, from_data.password,db)

    if not user:
        return 'Failed Authentication.'

    token = create_access_token(user.username,user.id,user.role, timedelta(minutes= 30))
    return {'access_token' : token, 'tokey_type' : 'bearer'}


@route.put('/edituser')
def update_user(user: user_dependancey,db: db_dependancey, update_info: UpdateUser):

    if user is None:
        raise HTTPException(status_code= 404, detail='Failed Authentication')
    
    find = db.query(Users).filter(Users.id == user.get('id')). first()
    update = update_info.model_dump(exclude_unset= True)

    for key,value in update.items():
        setattr(find,key, value)

    db.commit()
    return JSONResponse(status_code= 200, content={'Message' : 'User Updated Successfully'})

@route.put('/passwordchange')
def update_password(user: user_dependancey, db : db_dependancey, update_pass : UpdatePassword):

    if user is None:
        raise HTTPException(status_code= 404, detail='Failed Authentication')

    find = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(update_pass.current_password,find.hash_password):
        raise HTTPException(status_code= 401, detail='Wrong Password')

    find.hash_password = bcrypt_context.hash(update_pass.new_password)
    db.add(user)
    db.commit()
    return JSONResponse(status_code=200, content= {'Message' : 'Password Update Sucessfully'})


@route.get('/user')
def get_user(user: user_dependancey ,db: db_dependancey):
    if user is None:
        raise HTTPException(status_code=404, detail='Failed Authentication')

    curret_user = db.query(Users).filter(Users.id == user.get('id')).first()

    if curret_user is None:
        raise HTTPException(status_code=404, detail='User Not Found')

    return{
    'id' : curret_user.id,
    'email' : curret_user.email,
    'username'  : curret_user.username,
    'fastname'  : curret_user.fastname,
    'lastname'  : curret_user.lastname,
    'is_active'  : curret_user.is_active,
    'role'  : curret_user.role
    }
