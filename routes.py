from flask import Blueprint, request, redirect, render_template, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db.models import User, Genre, Book, CartItem
from db.database import session_scope
from sqlalchemy.orm import joinedload

bp = Blueprint('main', __name__)

### --- Аутентификация --- ###

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with session_scope() as session:
            user = session.query(User).filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session.expunge(user)
                login_user(user)
                return redirect(url_for('main.profile'))
            else:
                flash('Неправильный email или пароль')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        password_hash = generate_password_hash(password)

        with session_scope() as session:
            if session.query(User).filter_by(email=email).first():
                flash('Пользователь с таким email уже существует')
                return redirect(url_for('main.register'))

            user = User(
                username=username,
                email=email,
                phone_number=phone,
                password_hash=password_hash
            )
            session.add(user)

        flash('Регистрация успешна! Теперь войдите в аккаунт.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template("profile.html", user=current_user)

### --- Вспомогательная функция жанров --- ###

def get_genre_hierarchy(session):
    root_genres = session.query(Genre).filter_by(parent_id=None).all()

    def serialize(genre):
        return {
            'id': genre.id,
            'name': genre.name,
            'subgenres': [serialize(sub) for sub in genre.subgenres]
        }

    return [serialize(g) for g in root_genres]

### --- Главная страница --- ###

@bp.route('/')
def index():
    genre_id = request.args.get('genre_id', type=int)
    search_query = request.args.get('search', '', type=str)

    with session_scope() as session:
        query = session.query(Book).options(joinedload(Book.genres))

        if genre_id:
            query = query.join(Book.genres).filter(Genre.id == genre_id)

        if search_query:
            query = query.filter(Book.name.ilike(f'%{search_query}%'))

        books = query.all()

        top_books = (
            session.query(Book)
            .options(joinedload(Book.genres))
            .order_by(Book.rating.desc())
            .limit(3)
            .all()
        )

        books_data = [
            {
                "id": book.id,
                "name": book.name,
                "author": book.author,
                "price": book.price,
                "cover": book.cover,
                "rating": book.rating,
                "genres": [genre.name for genre in book.genres],
            }
            for book in books
        ]

        top_books_data = [
            {
                "name": book.name,
                "author": book.author,
                "cover": book.cover,
                "rating": book.rating,
            }
            for book in top_books
        ]

        genres_tree = get_genre_hierarchy(session)

    return render_template(
        "index.html",
        books=books_data,
        top_books=top_books_data,
        genres=genres_tree
    )

### --- Регистрация маршрутов --- ###

def register_routes(app):
    app.register_blueprint(bp)


@bp.route('/book/<int:book_id>')
def book_detail(book_id):
    with session_scope() as session:
        book = session.query(Book).options(joinedload(Book.genres)).get(book_id)
        if not book:
            return render_template('404.html'), 404

        # Создаём копию данных до выхода из with
        book_data = {
            'id': book.id,
            'name': book.name,
            'author': book.author,
            'price': book.price,
            'cover': book.cover,
            'description': book.description,
            'rating': book.rating,
            'year': getattr(book, 'year', None),
            'genres': [g.name for g in book.genres]
        }

    return render_template('book_detail.html', book=book_data)


@bp.route('/cart/add/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    from db.models import CartItem, Book
    with session_scope() as session:
        book = session.query(Book).get(book_id)
        if not book:
            flash("Книга не найдена.")
            return redirect(url_for('main.index'))

        # Проверка, есть ли уже эта книга в корзине
        item = session.query(CartItem).filter_by(user_id=current_user.id, book_id=book_id).first()
        if item:
            item.quantity += 1
        else:
            new_item = CartItem(user_id=current_user.id, book_id=book_id, quantity=1)
            session.add(new_item)

        flash("Книга добавлена в корзину!")
    return redirect(url_for('main.book_detail', book_id=book_id))

@bp.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def leave_review(book_id):
    flash("Форма отзыва пока не реализована.")
    return redirect(url_for('main.book_detail', book_id=book_id))

@bp.route('/cart')
@login_required
def show_cart():
    from db.models import CartItem, Book

    with session_scope() as session:
        items = (
            session.query(CartItem)
            .filter_by(user_id=current_user.id)
            .join(Book)
            .all()
        )

        total = sum(item.book.price * item.quantity for item in items)

        # Экспортируем объекты как есть — шаблон использует item.book.name и т.д.
        session.expunge_all()  # отсоединить от сессии

    return render_template("cart.html", cart_items=items, total=total)

from db.database import session_scope

@bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    from db.models import CartItem  # если не импортирован выше

    with session_scope() as session:
        item = session.query(CartItem).get(item_id)

        if item and item.user_id == current_user.id:
            session.delete(item)
            session.commit()

    return redirect(url_for('main.show_cart'))

@bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    with session_scope() as session:
        item = session.get(CartItem, item_id)

        if item and item.user_id == current_user.id:
            action = request.form.get('action')

            if action == 'increase':
                item.quantity += 1
            elif action == 'decrease' and item.quantity > 1:
                item.quantity -= 1

            session.commit()

    return redirect(url_for('main.show_cart'))


@bp.route('/checkout')
@login_required
def checkout():
    return "Оформление заказа в разработке"



