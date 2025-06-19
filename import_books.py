import json
from db.database import session_scope, init_db
from db.models import Book, Genre
from pathlib import Path

init_db() 

file_path = Path("books_catalog.json")

with open(file_path, encoding="utf-8") as f:
    books_data = json.load(f)

with session_scope() as session:
    genre_cache = {}

    for item in books_data:
        genre_name = item["genre"]
        
        if genre_name not in genre_cache:
            genre = session.query(Genre).filter_by(name=genre_name).first()
            if not genre:
                genre = Genre(name=genre_name)
                session.add(genre)
                session.flush() 
            genre_cache[genre_name] = genre
        else:
            genre = genre_cache[genre_name]

        book = Book(
            name=item["title"],
            author=item["author"],
            price=int(item["price"]),
            cover=item["cover"],
            description=item["description"],
            rating=item["rating"]
        )

        book.genres.append(genre)
        session.add(book)

    print("✅ Импорт завершён успешно.")
