import json
from db.database import session_scope, init_db
from db.models import Book, Genre
from pathlib import Path

SUBGENRE_TO_PARENT = {
    "Фантастика": "Художественная литература",
    "Фэнтези": "Художественная литература",
    "Приключения": "Художественная литература",
    "Роман": "Художественная литература",
    "Детектив": "Художественная литература",
    "Научная литература": "Нехудожественная литература",
    "Саморазвитие": "Нехудожественная литература",
    "История": "Нехудожественная литература",
    "Бизнес": "Бизнес-литература",
    "Детская литература": "Детская литература"
}

init_db()
file_path = Path("books_catalog.json")

with open(file_path, encoding="utf-8") as f:
    books_data = json.load(f)

with session_scope() as session:
    genre_cache = {}

    for item in books_data:
        subgenre_name = item["genre"]
        parent_name = SUBGENRE_TO_PARENT.get(subgenre_name)

        if parent_name:
            parent_key = f"parent:{parent_name}"
            if parent_key not in genre_cache:
                parent_genre = session.query(Genre).filter_by(name=parent_name, parent_id=None).first()
                if not parent_genre:
                    parent_genre = Genre(name=parent_name)
                    session.add(parent_genre)
                    session.flush()
                genre_cache[parent_key] = parent_genre
            else:
                parent_genre = genre_cache[parent_key]
        else:
            parent_genre = None

        subgenre_key = f"{parent_name}:{subgenre_name}" if parent_genre else subgenre_name
        if subgenre_key not in genre_cache:
            genre = session.query(Genre).filter_by(name=subgenre_name).first()
            if not genre:
                genre = Genre(name=subgenre_name, parent=parent_genre)
                session.add(genre)
                session.flush()
            genre_cache[subgenre_key] = genre
        else:
            genre = genre_cache[subgenre_key]

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
