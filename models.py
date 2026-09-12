from database import Base
from sqlalchemy import Column,Integer,String,Boolean,DateTime, ForeignKey
from datetime import datetime



class Users(Base):

    __tablename__ = 'users'

    id = Column(Integer,primary_key= True, index= True)
    email = Column(String,unique= True)
    username = Column(String,unique= True)
    fastname = Column(String)
    lastname = Column(String)
    hash_password = Column(String)
    is_active = Column(Boolean, default= True)
    role = Column(String)

class Books(Base):

    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index= True)
    title = Column(String)
    author = Column(String)
    category = Column(String)
    discription = Column(String)
    price = Column(Integer, default= 0.0)
    total_copies = Column(Integer,default= 5)
    available_copies = Column(Integer, default= 3)
    cover_image = Column(String, nullable= True)
    create_at = Column(DateTime,default= datetime.now)


class Reservations(Base):

    __tablename__ = 'reservations'

    id = Column(Integer, primary_key=True, index= True)
    book_id = Column(Integer, ForeignKey('books.id') )
    user_id = Column(Integer, ForeignKey('users.id'))
    reservation_date = Column(DateTime, default= datetime.now)
    status = Column(String,default='pending')

class IssueRecords(Base):

    __tablename__ = 'issue_records'

    id = Column(Integer,primary_key=True, index= True)
    book_id = Column(Integer, ForeignKey('books.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    issue_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime)
    return_date = Column(DateTime, nullable= True)
    status = Column(String, default='issued')
    fine_amount = Column(Integer, default= 0.0)
    fine_paid = Column(Boolean, default= False)