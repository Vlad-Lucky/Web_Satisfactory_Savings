import os
import shutil
from sqlalchemy.orm import Session
from source_code.data import db_session
from flask.helpers import get_root_path
from source_code.data.users import Users
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired
from source_code.data.savings import Savings
from source_code.data.sessions import Sessions
from flask import redirect, send_from_directory
from flask import Flask, render_template, request
from source_code.data.privileges import Privileges
from source_code.misc.generating_ids import generate_filename
from source_code.constants import SITE_SECRET_KEY, INFO_DB_PATH
from source_code.misc.payment import make_session, QiwiPaymentStatus
from source_code.misc.payment_generation import generate_help_project_payload
from source_code.site.site_errors import NOT_ALLOWED, NOT_FOUND, SESSION_IS_OFFLINE
from source_code.save_parser.satisfactory_save_parser import SatisfactorySaveParser
from flask_login import current_user, LoginManager, login_user, login_required, logout_user
from source_code.site.forms import RegisterForm, SigninForm, SessionsAddForm, SessionsChoosingEditingForm, \
    SessionsEditForm, SessionOnlineForm


# метод для получения файлов из корневой папки source_code
def source_code_url_rule(filename, cut_source_code=True):
    value = app.send_file_max_age_default
    if value is None:
        max_age = None
    else:
        max_age = int(value.total_seconds())
    filename = filename.replace('\\', '/')
    if cut_source_code:
        filename = filename.lstrip('source_code').lstrip('/')
    return send_from_directory('', filename, max_age=max_age)


app = Flask(__name__, root_path=f'{get_root_path("")}/source_code',
            template_folder='site/templates', static_folder='site/static')
# добавление правила из корневой папки source_code
app.add_url_rule(f'/source_code/<path:filename>', endpoint='source_code', view_func=source_code_url_rule)

login_manager = LoginManager()
load_user_session = Session()


@login_manager.user_loader
def load_user(user_id):
    return load_user_session.query(Users).filter(Users.id == user_id).first()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index/', methods=['GET', 'POST'])
def index():
    db_sess = db_session.create_session()
    sessions = db_sess.query(Sessions)
    sessions_ids = [session.session_id for session in sessions]
    errors = []
    if request.method == 'POST':
        # получение тега name у file_input`ов, id сессий которых ЕСТЬ в активных сессиях
        names = [elem for elem in request.files
                 if elem.startswith('load_saving_inp_') and elem[len('load_saving_inp_'):].isdigit()
                 and int(elem[len('load_saving_inp_'):]) in sessions_ids]
        for name in names:
            session_id = int(name[len('load_saving_inp_'):])
            session = sessions.filter(Sessions.session_id == session_id).first()
            if session.is_online and session.last_opener_id != current_user.id:
                return render_template('error.html', **NOT_ALLOWED)
            # сохраняем файл как ненужное
            file = request.files[name]
            saving_path = generate_filename('source_code/db/trash/adding_sessions/savings')
            file.save(saving_path)
            # проверка на правильность сохранения
            sav_parser1 = SatisfactorySaveParser(session.savings[-1].saving_path)
            sav_parser2 = SatisfactorySaveParser(saving_path)
            if not sav_parser2.is_correct_save():
                errors.append({'session_id': session_id, 'text': 'Sav file is incorrect'})
                break
            if not sav_parser1.is_next_save(saving_path):
                errors.append(
                    {'session_id': session_id,
                     'text': 'Seems like you were not playing on this save or save is not the next after current'})
                break
            # если всё нормально, то перемещаем его
            new_saving_path = generate_filename('source_code/db/all_savings/savings')
            shutil.move(saving_path, new_saving_path)
            # добавляем сессию в активные
            saving = Savings(owner_id=current_user.id, saving_path=new_saving_path)
            db_sess.add(saving)
            db_sess.commit()

            session.savings.append(saving)
            db_sess.commit()
    db_sess.close()
    return render_template('index.html', sessions=sessions)


@app.route('/sessions/info/show/<int:session_id>')
@login_required
def sessions_info_show(session_id):
    db_sess = db_session.create_session()
    session = db_sess.query(Sessions).filter(Sessions.session_id == session_id).first()
    info = session.info
    db_sess.close()
    if not session.is_online:
        return render_template('error.html', **SESSION_IS_OFFLINE)
    return render_template('sessions_info_show.html', info=info)


# перевод сессии в оффлайн
@app.route('/sessions/info/offline/<int:session_id>')
@login_required
def sessions_info_offline(session_id):
    db_sess = db_session.create_session()
    session = db_sess.query(Sessions).filter(Sessions.session_id == session_id).first()
    if not session.is_online or session.last_opener_id != current_user.id:
        db_sess.close()
        return render_template('error.html', **NOT_ALLOWED)
    session.is_online = False
    db_sess.commit()
    db_sess.close()
    return redirect('/')


# перевод сессии в онлайн
@app.route('/sessions/info/online/<int:session_id>', methods=['GET', 'POST'])
@login_required
def sessions_info_online(session_id):
    db_sess = db_session.create_session()
    session = db_sess.query(Sessions).filter(Sessions.session_id == session_id).first()
    if session.is_online or session.last_opener_id != current_user.id:
        db_sess.close()
        return render_template('error.html', **NOT_ALLOWED)
    form = SessionOnlineForm()
    if form.validate_on_submit():
        # сбор информации о сессии
        info = {'game_session_id': form.game_session_id.data, 'game_session_type': form.game_session_type.data}
        if form.game_session_type.data == '1':
            info['owner_platform'] = form.owner_platform.data
            info['owner_account_name'] = form.owner_account_name.data

        # сохранение информации о сессии
        session.is_online = True
        session.last_opener_id = current_user.id
        session.info = info
        db_sess.commit()
        db_sess.close()
        return redirect('/')
    db_sess.close()
    return render_template('sessions_info_online.html', form=form)


@app.route('/sessions/edit/<int:session_id>', methods=['GET', 'POST'])
@login_required
def sessions_edit(session_id):
    if not any([session.session_id == session_id for session in current_user.sessions]):
        return render_template('error.html', **NOT_ALLOWED)
    changing = request.args.get('changing', default=None, type=str)
    # если в строке есть запрос, какие данные изменять, то предъявляем форму изменения данных
    if changing is not None:
        try:
            changing = changing.split(',')
            # делаем так, что указанные изменяемые данные - обязательны
            if not any(changing) or any([elem not in ['name', 'description', 'photo'] for elem in changing]):
                return render_template('error.html', **NOT_FOUND)
            form = SessionsEditForm()
            if 'name' in changing:
                form.session_name.validators.append(DataRequired())
            if 'description' in changing:
                form.session_description.validators.append(DataRequired())
            if 'photo' in changing:
                form.session_photo.validators.append(DataRequired())
            if form.validate_on_submit():
                # изменяем иформацию о сохранении
                db_sess = db_session.create_session()
                session = db_sess.query(Sessions).filter(Sessions.session_id == session_id).first()

                # сохранение всё как ненужное для промежуточного анализа
                if form.session_photo.data:
                    photo_path_secured = secure_filename(form.session_photo.data.filename)
                    photo_path = generate_filename(
                        'source_code/db/trash/adding_sessions/photos', f'{photo_path_secured}')
                    form.session_photo.data.save(photo_path)
                    # если всё нормально, то перемещаем их
                    new_photo_path = generate_filename(
                        'source_code/db/all_savings/photos', f'{photo_path_secured}')
                    shutil.move(photo_path, new_photo_path)

                    session.photo_path = new_photo_path
                if form.session_name.data:
                    session.name = form.session_name.data
                if form.session_description.data:
                    session.description = form.session_description.data
                db_sess.commit()
                db_sess.close()

                return redirect('/')
            return render_template('sessions_edit.html', form=form, changing=changing)
        except Exception:
            return render_template('error.html', **NOT_FOUND)
    # иначе форму выбора данных
    form = SessionsChoosingEditingForm()
    if form.validate_on_submit():
        # перенапрвляем в такую следующую ссылку, где есть указанные пользователем изменяемые данные
        changing = []
        if form.change_session_name.data:
            changing.append('name')
        if form.change_session_description.data:
            changing.append('description')
        if form.change_session_photo.data:
            changing.append('photo')
        if any(changing):
            return redirect(f'/sessions/edit/{session_id}?changing={",".join(changing)}')
    return render_template('sessions_choosing_editing.html', form=form)


@app.route('/sessions/add', methods=['GET', 'POST'])
@login_required
def sessions_add():
    if not any([privilege.key_name == 'session_creator' for privilege in current_user.privileges]):
        return render_template('error.html', **NOT_ALLOWED)
    form = SessionsAddForm()
    if form.validate_on_submit():
        # сохранение всего как ненужное для промежуточного анализа
        saving_path = generate_filename('source_code/db/trash/adding_sessions/savings')
        form.saving.data.save(saving_path)

        photo_path_secured = secure_filename(form.session_photo.data.filename)
        photo_path = generate_filename('source_code/db/trash/adding_sessions/photos', f'{photo_path_secured}')
        form.session_photo.data.save(photo_path)

        # проверка на правильность сохранения
        sav_parser = SatisfactorySaveParser(saving_path)
        if not sav_parser.is_correct_save():
            form.saving.errors.append('Sav file is incorrect')
            return render_template('sessions_add.html', form=form)

        # если всё нормально, то перемещаем их
        new_saving_path = generate_filename('source_code/db/all_savings/savings')
        shutil.move(saving_path, new_saving_path)
        new_photo_path = generate_filename('source_code/db/all_savings/photos', f'{photo_path_secured}')
        shutil.move(photo_path, new_photo_path)

        # добавляем сессию в активные
        db_sess = db_session.create_session()
        saving = Savings(owner_id=current_user.id, saving_path=new_saving_path)
        db_sess.add(saving)
        db_sess.commit()

        session = Sessions(creator_id=current_user.id, description=form.session_description.data,
                           photo_path=new_photo_path, name=form.session_name.data)
        session.savings.append(saving)
        db_sess.add(session)
        db_sess.commit()

        db_sess.close()

        current_user.sessions.append(session)
        load_user_session.commit()

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
        login_user(user, remember=form.remember_me.data)
        db_sess.close()
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
