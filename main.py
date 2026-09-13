from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import JSONResponse
import models
from models import Books,Reservations,IssueRecords
from database import engine,SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from router import auth,admin
from router.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind = engine)
app.include_router(auth.route)
app.include_router(admin.route)


def get_db():
    db = SessionLocal()

    try: 
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]
user_dependancy = Annotated[Session, Depends(get_current_user)]


@app.get('/books/all')
def all_books(db:db_dependency):   
    return db.query(Books).all()

@app.get('/books/{book_id}')
def secific_books(user : user_dependancy,db:db_dependency, book_id : int):
    if user is None: 
        raise HTTPException(status_code=404, detail= 'Failed Authentication')

    find = db.query(Books).filter(Books.id == book_id).first()
    if find is None: 
             raise HTTPException(status_code=404, detail= 'Book Not Found')
    return find


@app.get('/reserve/{book_id}')
def reserved_books(user : user_dependancy,db:db_dependency, book_id : int):
    if user is None: 
        raise HTTPException(status_code=404, detail= 'Failed Authentication')

    find = db.query(Books).filter(Books.id == book_id).first()
    if find is None: 
         raise HTTPException(status_code=404, detail= 'Book Not Found')

    reserve_model = Reservations(
        book_id = book_id,
        user_id = user.get('id'),
        status = 'pending'
    )

    db.add(reserve_model)
    db.commit()
    return JSONResponse(status_code=201, content={'Message' : 'Book reserved Sucessfully.'})



@app.get('/reserve/cencel/{reservation_id}')
def reserved_cencel_books(user : user_dependancy,db:db_dependency, reservation_id : int):
    if user is None: 
        raise HTTPException(status_code=404, detail= 'Failed Authentication')

    find = db.query(Reservations).filter(Reservations.id == reservation_id).first()
    if find is None: 
         raise HTTPException(status_code=404, detail= 'Book Not Found')

    find.status = 'cancelled'
    db.commit()
    return JSONResponse(status_code=201, content={'Message' : 'Reservation Cencelled Sucessfully.'})


@app.get('/reserve/my')
def my_resvered_books(user : user_dependancy,db:db_dependency):
    if user is None: 
        raise HTTPException(status_code=404, detail= 'Failed Authentication')

    find = db.query(Reservations).filter(Reservations.user_id == user.get('id')).all()
    if find is None: 
         raise HTTPException(status_code=404, detail= 'Reservation Not Found')

    return find

@app.get('/issue/my')
def my_issued_books(user : user_dependancy,db:db_dependency):
    if user is None: 
        raise HTTPException(status_code=404, detail= 'Failed Authentication')

    find = db.query(IssueRecords).filter(IssueRecords.user_id == user.get('id'),
                                         IssueRecords.status == 'issued').all()
    if find is None: 
         raise HTTPException(status_code=404, detail= 'Issed Books Not Found')

    return find



