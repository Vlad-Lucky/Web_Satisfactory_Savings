import os

import flask
from flask import Flask, render_template, request
from flask_login import current_user, LoginManager, login_user, login_required, logout_user

from source_code.constants import PRIVILEGES, SITE_SECRET_KEY, INFO_DB_PATH
from source_code.data import db_session
from source_code.data.privileges import Privileges
from source_code.data.users2privileges import Users2Privileges
from source_code.data.users import Users
import requests
from flask import redirect

from source_code.misc.payment import make_session, QiwiPaymentStatus
from source_code.misc.payment_generation import generate_help_project_payload
from source_code.site.forms import RegisterForm, SigninForm

app = Flask(__name__)
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Users).filter(Users.id == user_id).first()


@app.route('/')
@app.route('/index/')
def index():
    return render_template('base.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Users).filter(Users.login == form.login.data).first():
            return render_template('register.html', form=form, modal_message="Such user already exists")

        user = Users(login=form.login.data, discord=form.discord_login.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        login_user(user, remember=form.remember_me.data)
        return redirect("/")
    return render_template('register.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if form.validate_on_submit():
        if form.login_submit.data:
            db_sess = db_session.create_session()
            user = db_sess.query(Users).filter(Users.login == form.login.data).first()
            login_user(user, remember=form.login_remember_me.data)
            return redirect("/")
        elif form.discord_submit.data:
            db_sess = db_session.create_session()
            user = db_sess.query(Users).filter(Users.discord == form.discord_login.data).first()
            login_user(user, remember=form.discord_remember_me.data)
            return redirect("/")
    return render_template('signin.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# помощь проекту с выбором цены оплаты
@app.route('/help_project', methods=['GET', 'POST'])
def help_project():
    if request.method == 'POST':
        if 'generate' not in request.form:
            return render_template('help_project.html', action='generate', not_load_help_project_footer=True)
        amount = int(request.form['amount'])
        if current_user.is_authenticated:
            payload = generate_help_project_payload(amount, for_user_id=current_user.id)
        else:
            payload = generate_help_project_payload(amount)
        return redirect(
            f'/help_project/{payload["billId"]}/{payload["payUrl"].split("?invoice_uid=")[1].split("?")[0]}')
    else:
        return render_template('help_project.html', action='generate', not_load_help_project_footer=True)


# проверка платежа помощи проекту
@app.route('/help_project/<bill_id>/<invoice_uid>/', methods=['GET', 'POST'])
def help_project_check(bill_id, invoice_uid):
    if request.method == 'POST':
        if 'check' not in request.form:
            return render_template(
                'help_project.html', action='check', payload=f'https://oplata.qiwi.com/form/?invoice_uid={invoice_uid}',
                not_load_help_project_footer=True)
        session = make_session()
        response = session.get(f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}').json()
        if 'status' not in response.keys():
            payload_message = 'No such payload'
        else:
            status = response['status']['value']
            payload_message = 'No payload answer'
            if status == QiwiPaymentStatus.WAITING.value:
                payload_message = 'Payload is waiting for pay'
            elif status == QiwiPaymentStatus.EXPIRED.value:
                payload_message = 'Payload is expired'
            elif status == QiwiPaymentStatus.REJECTED.value:
                payload_message = 'Payload is rejected'
            elif status == QiwiPaymentStatus.PAID.value:
                payload_message = 'Payload is paid. Thanks for helping'
                # добавление привилегии контрибьютора пользователю
                if current_user.is_authenticated:
                    db_sess = db_session.create_session()
                    if not any(db_sess.query(Users2Privileges).filter(
                            Users2Privileges.user_id == current_user.id and
                            Users2Privileges.privilege_id == PRIVILEGES['contributor'])):
                        user2privilege = Users2Privileges(user_id=current_user.id,
                                                          privilege_id=PRIVILEGES['contributor'])
                        db_sess.add(user2privilege)
                    db_sess.commit()
                    payload_message += '. You have got the role in discord.'
        return render_template(
            'help_project.html', action='check', payload=f'https://oplata.qiwi.com/form/?invoice_uid={invoice_uid}',
            payload_message=payload_message, not_load_help_project_footer=True)
    else:
        return render_template(
            'help_project.html', action='check', payload=f'https://oplata.qiwi.com/form/?invoice_uid={invoice_uid}',
            not_load_help_project_footer=True)


def run():
    cond = os.path.exists(INFO_DB_PATH)
    db_session.global_init(INFO_DB_PATH)
    if not cond:
        session = db_session.create_session()
        privilege = Privileges(privilege_id=PRIVILEGES['contributor'], name='Contributor', is_displaying=True)
        session.add(privilege)
        session.commit()

    login_manager.init_app(app)
    app.config['SECRET_KEY'] = SITE_SECRET_KEY
    app.run(host='127.0.0.1', port=8080)
