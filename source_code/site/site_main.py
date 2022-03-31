import flask
from flask import Flask, render_template, request
from flask_login import current_user, LoginManager

from source_code.constants import PRIVILEGES
from source_code.data import db_session
from source_code.data.users2privileges import Users2Privileges
from source_code.data.users import Users
import requests

from source_code.misc.payment import make_session, PaymentStatus
from source_code.misc.payment_generation import generate_help_project_payload

app = Flask(__name__)
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Users).get(user_id)


@app.route('/')
def index():
    return render_template('base.html')


# помощь проекту с выбором цены оплаты
@app.route('/help_project', methods=['GET', 'POST'])
def help_project():
    if request.method == 'POST':
        if 'generate' not in request.form:
            return render_template('help_project.html', action='generate', not_load_help_project_footer=True)
        amount = int(request.form['amount'])
        if current_user.is_authenticated:
            payload = generate_help_project_payload(amount, for_user_id=current_user.user_id)
        else:
            payload = generate_help_project_payload(amount)
        return flask.redirect(
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
            if status == PaymentStatus.WAITING.value:
                payload_message = 'Payload is waiting for pay'
            elif status == PaymentStatus.EXPIRED.value:
                payload_message = 'Payload is expired'
            elif status == PaymentStatus.REJECTED.value:
                payload_message = 'Payload is rejected'
            elif status == PaymentStatus.PAID.value:
                payload_message = 'Payload is paid. Thanks for helping'
                # добавление привилегии контрибьютора пользователю
                if current_user.is_authenticated:
                    db_sess = db_session.create_session()
                    if not any(db_sess.query(Users2Privileges).filter(
                            Users2Privileges.user_id == current_user.user_id and
                            Users2Privileges.privilege_id == PRIVILEGES['contributor'])):
                        user2privilege = Users2Privileges()
                        user2privilege.user_id = current_user.user_id
                        user2privilege.privilege_id = PRIVILEGES['contributor']
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
    login_manager.init_app(app)
    app.run(port=8080, host='127.0.0.1')
