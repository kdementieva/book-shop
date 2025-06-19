from flask import Blueprint, request, redirect, render_template, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from db.models import User
from db.database import session_scope
from werkzeug.security import check_password_hash

bp = Blueprint('auth', __name__)

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
                return redirect(url_for('auth.profile'))
            else:
                flash('Неправильный email или пароль')
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        password_hash = generate_password_hash(password)

        with session_scope() as session:
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                flash('Пользователь с таким email уже существует')
                return redirect(url_for('auth.register'))

            user = User(
                username=username,
                email=email,
                phone_number=phone,
                password_hash=password_hash
            )
            session.add(user)

        flash('Регистрация успешна! Теперь войдите в аккаунт.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template("profile.html", user=current_user)




def register_routes(app):
    app.register_blueprint(bp)