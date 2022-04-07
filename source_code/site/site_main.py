import os
import shutil

from flask import redirect
from werkzeug.utils import secure_filename

from source_code.data import db_session
from source_code.data.savings import Savings
from source_code.data.sessions import Sessions
from source_code.data.users import Users
from flask import Flask, render_template, request
from source_code.data.privileges import Privileges
from source_code.misc.generating_ids import generate_filename
from source_code.save_parser.bytes_parser import BytesParserSpecializer
from source_code.save_parser.satisfactory_save import get_data
from source_code.site.forms import RegisterForm, SigninForm, SessionsAddForm
from source_code.misc.payment import make_session, QiwiPaymentStatus
from source_code.constants import SITE_SECRET_KEY, INFO_DB_PATH
from source_code.misc.payment_generation import generate_help_project_payload
from flask_login import current_user, LoginManager, login_user, login_required, logout_user

from source_code.site.site_errors import NOT_ALLOWED

app = Flask(__name__)
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(Users).filter(Users.id == user_id).first()


@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html')


@app.route('/sessions/add', methods=['GET', 'POST'])
@login_required
def sessions_add():
    if not any([privilege.key_name == 'session_creator' for privilege in current_user.privileges]):
        return render_template('error.html', **NOT_ALLOWED)
    form = SessionsAddForm()
    if form.validate_on_submit():
        # сохранение всего как ненужное для промежуточного анализа
        saving_path_secured = secure_filename(form.saving.data.filename)
        saving_path = generate_filename(
            'source_code/db/trash/adding_sessions/savings', f'{current_user.id}_{saving_path_secured}')
        form.saving.data.save(saving_path)

        photo_path_secured = secure_filename(form.photo.data.filename)
        photo_path = generate_filename(
            'source_code/db/trash/adding_sessions/photos', f'{current_user.id}_{photo_path_secured}')
        form.photo.data.save(photo_path)

        # проверка на правильность сохранения
        try:
            sav_parser = BytesParserSpecializer(saving_path)
            get_data(sav_parser)
        except Exception:
            form.saving.errors.append('Sav file is incorrect')
            return render_template('sessions_add.html', form=form)

        # если всё нормально, то перемещаем их
        new_saving_path = generate_filename('source_code/db/all_savings/savings', f'{saving_path_secured}')
        shutil.move(saving_path, new_saving_path)
        new_photo_path = generate_filename('source_code/db/all_savings/photos', f'{photo_path_secured}')
        shutil.move(photo_path, new_photo_path)

        # добавляем сессию в активные
        db_sess = db_session.create_session()
        saving = Savings(owner_id=current_user.id, name=form.session_name.data,
                         description=form.session_description.data, saving_path=new_saving_path,
                         photo_path=new_photo_path)
        db_sess.add(saving)
        db_sess.commit()

        session = Sessions(saving_id=saving.saving_id)
        db_sess.add(session)
        db_sess.commit()

        db_sess.close()

        return redirect('/')
    return render_template('sessions_add.html', form=form)


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
        db_sess.close()

        login_user(user, remember=form.remember_me.data)
        return redirect("/")
    return render_template('register.html', form=form)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if form.validate_on_submit():
        if form.login_submit.data:
            # пользователь логинится благодаря логину
            db_sess = db_session.create_session()
            user = db_sess.query(Users).filter(Users.login == form.login.data).first()
            login_user(user, remember=form.login_remember_me.data)
            return redirect("/")
        elif form.discord_submit.data:
            # пользователь логинится благодаря дискорду
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

        # проверка на amount=str
        try:
            amount = int(request.form['amount'])
        except ValueError:
            return render_template('help_project.html', action='generate', not_load_help_project_footer=True)

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
            # проверка статуса платежа
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
                    privilege_contributor = db_sess.query(Privileges).filter(
                        Privileges.key_name == 'contributor').first()
                    user = db_sess.query(Users).filter(Users.id == current_user.id).first()
                    user.privileges.append(privilege_contributor)
                    db_sess.commit()
                    db_sess.close()
                    payload_message += '. You have already got the role in discord.'
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
        db_sess = db_session.create_session()

        privilege = Privileges(key_name='contributor', name='Contributor', is_displaying=True)
        db_sess.add(privilege)
        privilege = Privileges(key_name='session_creator', name='Session Creator', is_displaying=False)
        db_sess.add(privilege)

        db_sess.commit()
        db_sess.close()

    login_manager.init_app(app)
    app.config['SECRET_KEY'] = SITE_SECRET_KEY
    app.run(host='127.0.0.1', port=8080)
