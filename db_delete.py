from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, drop_database, create_database

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/book_shop"

engine = create_engine(DATABASE_URL)

if database_exists(engine.url):
    drop_database(engine.url)

print("✅ База данных создана заново.")
