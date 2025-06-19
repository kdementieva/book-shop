from flask import Flask
from config import settings
from db.database import init_db
from flask_login import LoginManager
from db.models import User
import routes

app = Flask(import_name=__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY

routes.register_routes(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from db.database import session_scope
    with session_scope() as session:
        user = session.query(User).get(int(user_id))
        session.expunge(user) 
        return user

if __name__ == '__main__':
    init_db()
    app.run(port=settings.APP_PORT, debug=settings.DEBUG)