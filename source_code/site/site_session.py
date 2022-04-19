import os
from flask import Flask
from flask_login import LoginManager
from source_code.data import db_session
from flask.helpers import get_root_path
from source_code.site.urls import SiteUrls
from source_code.data.privileges import Privileges
from source_code.constants import SITE_SECRET_KEY, INFO_DB_PATH, PRIVILEGES


def run():
    cond = os.path.exists(INFO_DB_PATH)
    db_session.global_init(INFO_DB_PATH)
    if not cond:
        db_sess = db_session.create_session()

        for privilege in PRIVILEGES:
            new_privilege = Privileges(**privilege)
            db_sess.add(new_privilege)

        db_sess.commit()
        db_sess.close()

    login_manager = LoginManager()
    load_user_session = db_session.create_session()

    app = Flask(__name__, root_path=f'{get_root_path("")}/source_code',
                template_folder='site/templates', static_folder='site/static')

    # общее добавление urls
    SiteUrls(app, load_user_session, login_manager).register()

    login_manager.init_app(app)
    app.config['SECRET_KEY'] = SITE_SECRET_KEY
    app.run(host='127.0.0.1', port=8080)
