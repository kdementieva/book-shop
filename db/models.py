from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

book_genre_association = Table(
    'book_genre', Base.metadata,
    Column('book_id', ForeignKey('books.id'), primary_key=True),
    Column('genre_id', ForeignKey('genres.id'), primary_key=True)
)

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone_number = Column(String(20))
    password_hash = Column(String(256), nullable=False)

    cart_items = relationship('CartItem', back_populates='user')
    orders = relationship('Order', back_populates='user')
    reviews = relationship('Review', back_populates='user')

class Genre(Base):
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    books = relationship('Book', secondary=book_genre_association, back_populates='genres')

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    author = Column(String(120), nullable=False)
    price = Column(Integer, nullable=False)
    cover = Column(String(120))
    description = Column(String(500))
    rating = Column(Float, default=0.0)

    genres = relationship('Genre', secondary=book_genre_association, back_populates='books')
    reviews = relationship('Review', back_populates='book')
    order_items = relationship('OrderItem', back_populates='book')

class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    quantity = Column(Integer, default=1)

    user = relationship('User', back_populates='cart_items')
    book = relationship('Book')

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    address = Column(String(200))
    
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')

class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    order = relationship('Order', back_populates='items')
    book = relationship('Book', back_populates='order_items')

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    review = Column(String(500))
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    grade = Column(Integer)

    user = relationship('User', back_populates='reviews')
    book = relationship('Book', back_populates='reviews')

