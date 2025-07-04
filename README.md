# BookShop

Это мой учебный проект — интернет-магазин книг. Я пишу его на Flask. В этом приложении можно регистрироваться, смотреть книги, добавлять их в корзину и делать заказы.

---

## Что умеет приложение

- Регистрация пользователей с подтверждением через SMS (имитация)
- Вход и выход из аккаунта
- Каталог книг с жанрами и поиском
- Страница книги с описанием и отзывами
- Добавление книг в корзину
- Оформление заказа (самовывоз или доставка)
- История заказов пользователя
- Добавление отзывов к книгам
- Страница 404

---

## Технологии

- Python 3.10+
- Flask
- Flask-Login
- Flask-SQLAlchemy
- SQLAlchemy
- PostgreSQL
- Jinja2 (шаблоны)
- Pydantic (для настроек из `.env`)
- HTML и CSS

---

## Установка и запуск

### 1. Клонировать репозиторий

```
git clone <адрес_репозитория>
cd book-shop
```

### 2. Создать виртуальное окружение

```
python -m venv venv
source venv/bin/activate      # Linux или macOS
venv\Scripts\activate         # Windows
```

### 3. Установить зависимости

```
pip install -r requirements.txt
```

---

## Настройки окружения

Создайте файл `.env` в корне проекта и добавьте туда такие строки:

```
SECRET_KEY=
DATABASE_URL=
APP_PORT=
```

---

## Работа с базой данных

### Чтобы сбросить базу данных и создать её заново:

```
python db_delete.py
```

### Чтобы загрузить книги в базу данных из файла JSON:

```
python import_book.py
```

Файл с книгами должен быть в проекте:

```
books_catalog.json
```

---

## Запуск приложения

```
python app.py
```

Приложение откроется по адресу:

```
http://127.0.0.1:5466
```

---

## Важные файлы проекта

| Файл | Что в нём |
|------|-----------|
| `app.py` | точка входа приложения Flask |
| `routes.py` | маршруты приложения (регистрация, каталог, корзина, заказы) |
| `models.py` | SQLAlchemy модели: User, Book, Genre, CartItem, Order, Review |
| `database.py` | подключение к базе данных и сессии |
| `config.py` | настройки через pydantic |
| `import_books.py` | скрипт для сброса базы данных |
| `import_book.py` | скрипт для загрузки книг из JSON |
| `.env` | переменные окружения |
| `requirements.txt` | зависимости Python |

---

## Как работает имитация SMS

Когда пользователь регистрируется, приложение придумывает случайный 4-значный код. Этот код сохраняется в сессии и показывается пользователю на экране (как будто это SMS). Потом пользователь должен ввести этот код на странице `/verify_sms`. Если код правильный — регистрация завершается.

---

## Лицензия

Этот проект сделан для учёбы.
