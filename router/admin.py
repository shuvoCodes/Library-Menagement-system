from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Annotated, Optional

from database import SessionLocal
from models import Users, Books, IssueRecords, Reservations
from router.auth import get_current_user


route = APIRouter()


class NewBook(BaseModel):
    title: str
    author: str
    category: str
    discription: str
    price: float = Field(default=0.0, ge=0)
    total_copies: int = Field(default=1, ge=1)


class UpdateBooks(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    discription: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    total_copies: Optional[int] = Field(default=None, ge=1)
    available_copies: Optional[int] = Field(default=None, ge=0)


class IssuedBook(BaseModel):
    book_id: int
    user_id: int




FINE_PER_DAY = 20
ISSUE_DAYS = 14


def calculate_fine(due_date: datetime, return_date: datetime):
    overdue_days = (return_date.date() - due_date.date()).days

    if overdue_days > 0:
        return round(overdue_days * FINE_PER_DAY, 2)

    return 0.0

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



@route.post("/admin/book_create")
def create_book(
    user: user_dependency,
    db: db_dependency,
    new_book: NewBook
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(
            status_code=401,
            detail="Only librarian can create books."
        )

    newbook = Books(
        title=new_book.title,
        author=new_book.author,
        category=new_book.category,
        discription=new_book.discription,
        price=new_book.price,
        total_copies=new_book.total_copies,
        available_copies=new_book.total_copies
    )

    db.add(newbook)
    db.commit()
    db.refresh(newbook)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Book added successfully.",
            "book_id": newbook.id
        }
    )


@route.put("/admin/book_update/{book_id}")
def update_book(
    user: user_dependency,
    db: db_dependency,
    update_books: UpdateBooks,
    book_id: int
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(
            status_code=401,
            detail="Only librarian can update books."
        )

    book = db.query(Books).filter(
        Books.id == book_id
    ).first()

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    update_data = update_books.model_dump(
        exclude_unset=True
    )

    if "total_copies" in update_data:

        old_total = book.total_copies
        new_total = update_data["total_copies"]

        difference = new_total - old_total

        book.total_copies = new_total

        book.available_copies += difference

        if book.available_copies < 0:
            book.available_copies = 0


    for key, value in update_data.items():

        if key != "total_copies":
            setattr(book, key, value)

    db.commit()
    db.refresh(book)

    return JSONResponse(
        status_code=200,
        content={
            "message": "Book updated successfully."
        }
    )



@route.delete("/admin/delete_book/{book_id}")
def delete_book(
    user: user_dependency,
    db: db_dependency,
    book_id: int
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(
            status_code=401,
            detail="Only librarian can delete books."
        )

    book = db.query(Books).filter(
        Books.id == book_id
    ).first()

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    
    active_issue = db.query(IssueRecords).filter(
        IssueRecords.book_id == book_id,
        IssueRecords.status == "issued"
    ).first()

    if active_issue is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a book that is currently issued."
        )

    db.delete(book)
    db.commit()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Book deleted successfully."
        }
    )



@route.post("/admin/issue_create")
def create_issue(
    user: user_dependency,
    db: db_dependency,
    isshu: IssuedBook
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(
            status_code=401,
            detail="Only librarian can issue books."
        )

 
    book = db.query(Books).filter(
        Books.id == isshu.book_id
    ).first()

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=400,
            detail="No available copies of this book."
        )

    member = db.query(Users).filter(
        Users.id == isshu.user_id
    ).first()

    if member is None:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )


    existing_issue = db.query(IssueRecords).filter(
        IssueRecords.book_id == isshu.book_id,
        IssueRecords.user_id == isshu.user_id,
        IssueRecords.status == "issued"
    ).first()

    if existing_issue is not None:
        raise HTTPException(
            status_code=400,
            detail="This user already has this book."
        )


    issue_date = datetime.now()
    due_date = issue_date + timedelta(days=ISSUE_DAYS)

    issue_record = IssueRecords(
        book_id=isshu.book_id,
        user_id=isshu.user_id,
        issue_date=issue_date,
        due_date=due_date,
        status="issued",
        fine_amount=0,
        fine_paid=False
    )


    book.available_copies -= 1


    reservation = db.query(Reservations).filter(
        Reservations.book_id == isshu.book_id,
        Reservations.user_id == isshu.user_id,
        Reservations.status == "pending"
    ).first()

    if reservation is not None:
        reservation.status = "approved"

    db.add(issue_record)
    db.commit()
    db.refresh(issue_record)

    return JSONResponse(
        status_code=201,
        content={
            "message": "Book issued successfully.",
            "issue_id": issue_record.id,
            "issue_date": issue_date.isoformat(),
            "due_date": due_date.isoformat()
        }
    )


@route.put("/admin/return_book/{issue_id}")
def return_book(
    user: user_dependency,
    db: db_dependency,
    issue_id: int
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(
            status_code=401,
            detail="Only librarian can return books."
        )

    issue = db.query(IssueRecords).filter(
        IssueRecords.id == issue_id
    ).first()

    if issue is None:
        raise HTTPException(
            status_code=404,
            detail="Issue record not found."
        )

    if issue.status == "returned":
        raise HTTPException(
            status_code=400,
            detail="This book has already been returned."
        )

    return_date = datetime.now()


    fine = calculate_fine(
        issue.due_date,
        return_date
    )


    issue.return_date = return_date
    issue.status = "returned"
    issue.fine_amount = fine

    book = db.query(Books).filter(
        Books.id == issue.book_id
    ).first()

    if book is not None:

        book.available_copies += 1


        if book.available_copies > book.total_copies:
            book.available_copies = book.total_copies

    db.commit()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Book returned successfully.",
            "fine_amount": fine,
            "fine_paid": False if fine > 0 else True
        }
    )



@route.put("/admin/fine/pay/{issue_id}")
def fine_paid(
    user: user_dependency,
    db: db_dependency,
    issue_id: int
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(
            status_code=401,
            detail="Only librarian can mark fine as paid."
        )


    issue = db.query(IssueRecords).filter(
        IssueRecords.id == issue_id
    ).first()

    if issue is None:
        raise HTTPException(
            status_code=404,
            detail="Issue record not found."
        )

    if issue.fine_amount is None or issue.fine_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="This issue has no fine."
        )
        
    if issue.fine_paid:
        raise HTTPException(
            status_code=400,
            detail="Fine has already been paid."
        )

    issue.fine_paid = True

    db.commit()

    return JSONResponse(
        status_code=200,
        content={
            "message": "Fine paid successfully.",
            "fine_amount": issue.fine_amount
        }
    )
