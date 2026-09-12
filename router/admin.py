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
from router.auth import get_current_user
from models import Books, IssueRecords,Reservations



route = APIRouter()

class newBooks(BaseModel):
    title : str
    author : str
    category : str
    discription : str
    price : float = Field(default=0.0, ge= 0)
    total_copies : int = Field(default=1)

class UpdateBooks(BaseModel):
    title : Optional[str] = Field(default= None)
    author : Optional[str] = Field(default= None)
    category : Optional[str] = Field(default= None)
    discription : Optional[str] = Field(default= None)
    price : Optional[float] = Field(default= None)
    total_copies : Optional[int] = Field(default= None)
    available_copies : Optional[int] = Field(default= None)

class IssuedBook(BaseModel):
     book_id : int
     user_id : int

FINE_PER_DAY = 20
def calculate_fine(due_date: datetime, return_date: datetime):
    overdue_days = (return_date.date() - due_date.date()).days
    if overdue_days > 0:
        return round(overdue_days * FINE_PER_DAY , 2)
    else:
        return 0.0

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(get_current_user)]

@route.post('/admin/book_create')
def create_book(user : user_dependency, db : db_dependency, new_book: newBooks):
    if user is None or user.get('role') != 'librarian':
         raise HTTPException(status_code= 404, detail='Failed Authentication.')

    newbook = Books(
         **new_book.model_dump(),
         available_copies = new_book.total_copies
    )

    db.add(newbook)
    db.commit()

    return JSONResponse(status_code=201, content={'Message' : 'Book Added Sucessfully.'})

@route.put('/admin/book_update/{book_id}')
def update_book(user: user_dependency, db: db_dependency, update_books: UpdateBooks, book_id : int):
    if user is None or user.get('role') != 'librarian':
        raise HTTPException(status_code= 404, detail='Failed Authentication.')

    find_book = db.query(Books).filter(Books.id == book_id).first()

    if find_book is None:
        raise HTTPException(status_code= 404, detail='Books Not Found.')

    update = update_books.model_dump(exclude_unset = True)

    for key,value in update.items():
           setattr(find_book,key,value)
    db.commit()

    return JSONResponse(status_code= 201, content={'Message' : 'Book Update Sucessfully.'})


@route.delete('/admin/delete_book/{book_id}')
def update_book(user: user_dependency, db: db_dependency, update_books: UpdateBooks, book_id : int):
    if user is None or user.get('role') != 'librarian':
        raise HTTPException(status_code= 404, detail='Failed Authentication.')

    find_book = db.query(Books).filter(Books.id == book_id).first()

    if find_book is None:
        raise HTTPException(status_code= 404, detail='Books Not Found.')

    db.query(Books).filter(Books.id == book_id).delete()

    db.commit()

    return JSONResponse(status_code= 201, content={'Message' : 'Book Delete Sucessfully.'})


@route.post('/admin/issue_create')
def create_book(user : user_dependency, db : db_dependency, isshu : IssuedBook):
    if user is None or user.get('role') != 'librarian':
         raise HTTPException(status_code= 404, detail='Failed Authentication.')

    book = db.query(Books).filter(Books.id == isshu.book_id).first()

    if book is None:
        raise HTTPException(status_code= 404, detail='Book Not Found.')

    member = db.query(Users).filter(Users.id == isshu.user_id).first()
    if member is None:
        raise HTTPException(status_code= 404, detail='User Not Found.')

    load_date = 14
    isshu_date = datetime.now

    isshu_book = IssueRecords(
        book_id = isshu.book_id,
        user_id = isshu.user_id,
        issue_date = isshu_date,
        due_date = isshu_date + timedelta(days= load_date),
        status = 'issued'
    )

    reserve = db.query(Reservations).filter(
        Reservations.book_id == isshu.book_id,
        Reservations.user_id == isshu.user_id,
        Reservations.status == 'pending'
    )
    if reserve is None:
        reserve.status = 'approved'
    

    db.add(isshu_book)
    db.commit()

    return JSONResponse(status_code=201, content={'Message' : 'Book Issued Sucessfully.'})

@route.put('/admin/return_book/{issue_id}')
def return_book(user: user_dependency, db: db_dependency, issue_id: int):

    if user is None or user.get('role') != 'librarian':
        raise HTTPException(status_code=401, detail='Failed Authentication')

    issue = db.query(IssueRecords).filter(IssueRecords.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue record not found')

    return_date = datetime.now
    fine = calculate_fine(issue.due_date, return_date)

    issue.return_date = return_date
    issue.status = 'returned'
    issue.fine_amount = fine

    book = db.query(Books).filter(Books.id == issue.book_id).first()
    if book is not None:
        book.available_copies += 1

    db.commit()

    return JSONResponse(status_code=201, content={'message': 'Book returned successfully', 'fine_amount': fine})

@route.put('/admin/fine/pay/{issue_id}')
def fine_paid(user: user_dependency, db: db_dependency, issue_id: int):

    if user is None or user.get('role') != 'librarian':
        raise HTTPException(status_code=401, detail='Failed Authentication')

    issue = db.query(IssueRecords).filter(IssueRecords.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail='Issue record not found')

    issue.fine_paid = True

    db.commit()

    return JSONResponse(status_code=200, content={'message': 'Fine paid successfully'})