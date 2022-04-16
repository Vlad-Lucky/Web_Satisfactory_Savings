import os
import flask
from flask import Flask
from sqlalchemy.orm import Session
from source_code.data import db_session
from flask.helpers import get_root_path
from source_code.data.users import Users
from source_code.site.urls import SiteUrls
from source_code.data.privileges import Privileges
from source_code.constants import SITE_SECRET_KEY, INFO_DB_PATH
from flask_login import LoginManager, login_required, logout_user


app = Flask(__name__, root_path=f'{get_root_path("")}/source_code',
            template_folder='site/templates', static_folder='site/static')

login_manager = LoginManager()
load_user_session = Session()

# общее добавление urls
SiteUrls(app, load_user_session).register()


@login_manager.user_loader
def load_user(user_id):
    return load_user_session.query(Users).filter(Users.id == user_id).first()


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return flask.redirect("/")


def run():
    global load_user_session
    cond = os.path.exists(INFO_DB_PATH)
    db_session.global_init(INFO_DB_PATH)
    if not cond:
        db_sess = db_session.create_session()

        privilege = Privileges(key_name='contributor', name='Contributor', is_displaying=True)
        db_sess.add(privilege)
        privilege = Privileges(key_name='session_creator', name='Session Creator', is_displaying=False)
        db_sess.add(privilege)

        db_sess.commit()
        db_sess.close()
    login_manager.init_app(app)
    load_user_session = db_session.create_session()
    app.config['SECRET_KEY'] = SITE_SECRET_KEY
    app.run(host='127.0.0.1', port=8080)
