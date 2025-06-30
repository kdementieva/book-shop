from flask import Blueprint, request, redirect, render_template, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db.models import User, Genre, Book, CartItem, Order, OrderItem, Review
from db.database import session_scope
from sqlalchemy.orm import joinedload
import random
from flask import session

bp = Blueprint('main', __name__)

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
                return redirect(url_for('main.index'))
            else:
                flash('Неправильный email или пароль')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

import random
from flask import session

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        with session_scope() as session_db:
            if session_db.query(User).filter_by(email=email).first():
                flash('Пользователь с таким email уже существует')
                return redirect(url_for('main.register'))

        verification_code = random.randint(1000, 9999)

        session['register_data'] = {
            'username': username,
            'email': email,
            'phone': phone,
            'password': password,
            'verification_code': str(verification_code)
        }

        flash(f"Ваш код для имитации SMS: {verification_code}")
        return redirect(url_for('main.verify_sms'))

    return render_template('register.html')


def get_genre_hierarchy(session):
    root_genres = session.query(Genre).filter_by(parent_id=None).all()

    def serialize(genre):
        return {
            'id': genre.id,
            'name': genre.name,
            'subgenres': [serialize(sub) for sub in genre.subgenres]
        }

    return [serialize(g) for g in root_genres]

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

def register_routes(app):
    app.register_blueprint(bp)


@bp.route('/book/<int:book_id>')
def book_detail(book_id):
    with session_scope() as session:
        book = session.query(Book).options(joinedload(Book.genres)).get(book_id)
        if not book:
            return render_template('404.html'), 404

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

        book_data['reviews'] = [
        {"review": r.review, "grade": r.grade, "user": {"username": r.user.username}}
        for r in book.reviews
        ]


    return render_template('book_detail.html', book=book_data)


@bp.route('/cart/add/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    from db.models import CartItem, Book
    with session_scope() as session:
        book = session.query(Book).get(book_id)
        if not book:
            flash("Книга не найдена.")
            return redirect(url_for('main.login'))

        item = session.query(CartItem).filter_by(user_id=current_user.id, book_id=book_id).first()
        if item:
            item.quantity += 1
        else:
            new_item = CartItem(user_id=current_user.id, book_id=book_id, quantity=1)
            session.add(new_item)

        flash("Книга добавлена в корзину!")
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
        session.expunge_all() 

    return render_template("cart.html", cart_items=items, total=total)

from db.database import session_scope

@bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    from db.models import CartItem 

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


from db.models import CartItem, Book, Order, OrderItem

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        delivery_method = request.form.get('delivery_method')
        address = request.form.get('address', '').strip()

        if delivery_method == 'door' and not address:
            flash("Пожалуйста, введите адрес доставки.")
            return redirect(url_for('main.checkout'))

        if delivery_method == 'pickup':
            address = "Самовывоз"

        with session_scope() as session:
            items = (
                session.query(CartItem)
                .filter_by(user_id=current_user.id)
                .join(Book)
                .all()
            )

            if not items:
                flash("Корзина пуста.")
                return redirect(url_for('main.index'))

            new_order = Order(
                user_id=current_user.id,
                status="pending",
                address=address
            )
            session.add(new_order)
            session.flush()

            for item in items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    book_id=item.book.id,
                    quantity=item.quantity,
                    price=item.book.price
                )
                session.add(order_item)

            for item in items:
                session.delete(item)

            flash("Заказ успешно оформлен!")

        return redirect(url_for('main.orders'))

    return render_template("checkout.html")


@bp.route('/orders')
@login_required
def orders():
    from db.models import Order, OrderItem, Book

    with session_scope() as session:
        user_orders = (
            session.query(Order)
            .filter_by(user_id=current_user.id)
            .order_by(Order.date.desc())
            .all()
        )

        for order in user_orders:
            for item in order.items:
                _ = item.book.name 

        session.expunge_all()

    return render_template("orders.html", orders=user_orders)

@bp.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def leave_review(book_id):
    with session_scope() as session:
        book = session.query(Book).get(book_id)
        if not book:
            flash("Книга не найдена.")
            return redirect(url_for('main.index'))

        existing = session.query(Review).filter_by(book_id=book_id, user_id=current_user.id).first()

        if request.method == 'POST':
            if existing:
                flash("Вы уже оставили отзыв на эту книгу.")
                return redirect(url_for('main.book_detail', book_id=book_id))

            review_text = request.form.get("review", "").strip()
            grade = int(request.form.get("grade", 0))

            if not (1 <= grade <= 5):
                flash("Оценка должна быть от 1 до 5.")
                return redirect(request.url)

            new_review = Review(
                review=review_text,
                grade=grade,
                book_id=book_id,
                user_id=current_user.id
            )
            session.add(new_review)
            
            reviews = session.query(Review).filter_by(book_id=book_id).all()
            book.rating = sum(r.grade for r in reviews + [new_review]) / (len(reviews) + 1)

            flash("Спасибо за отзыв!")
            return redirect(url_for('main.book_detail', book_id=book_id))

    return render_template("review_form.html")

@bp.route('/verify_sms', methods=['GET', 'POST'])
def verify_sms():
    if request.method == 'POST':
        code_entered = request.form.get('code', '').strip()
        reg_data = session.get('register_data')

        if not reg_data:
            flash("Сессия устарела. Зарегистрируйтесь снова.")
            return redirect(url_for('main.register'))

        if code_entered != reg_data['verification_code']:
            flash("Неправильный код.")
            return redirect(url_for('main.verify_sms'))

        with session_scope() as session_db:
            user = User(
                username=reg_data['username'],
                email=reg_data['email'],
                phone_number=reg_data['phone'],
                password_hash=generate_password_hash(reg_data['password'])
            )
            session_db.add(user)

        flash("Регистрация успешна! Теперь войдите в аккаунт.")
        session.pop('register_data', None)
        return redirect(url_for('main.login'))

    return render_template('verify_sms.html')
