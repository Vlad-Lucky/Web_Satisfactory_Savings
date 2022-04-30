import flask
import shutil
from flask import request
from sqlalchemy.orm import Session
from source_code.data import db_session
from source_code.data.users import Users
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired
from source_code.data.savings import Savings
from source_code.data.sessions import Sessions
from source_code.constants import SITE_CONSTANTS
from source_code.data.privileges import Privileges
from flask import redirect, Flask, send_from_directory
from source_code.misc.generating_ids import generate_filename
from source_code.misc.payment import make_session, QiwiPaymentStatus
from source_code.bots.discord.discord_session import get_discord_session
from source_code.misc.payment_generation import generate_help_project_payload
from source_code.save_parser.satisfactory_save_parser import SatisfactorySaveParser
from flask_login import current_user, login_user, login_required, LoginManager, logout_user
from source_code.site.site_errors import NOT_ALLOWED, NOT_FOUND, NOT_GUILDER_ERROR, UNAUTHORIZED_ERROR
from source_code.site.forms import RegisterForm, SigninForm, SessionsAddForm, SessionsChoosingEditingForm, \
    SessionsEditForm, SessionOnlineForm, ProfileForm


def render_template(*args, **kwargs) -> str:
    return flask.render_template(*args, **kwargs, **SITE_CONSTANTS)


class SiteUrls:
    def __init__(self, flask_app: Flask, load_user_session: Session, login_manager: LoginManager):
        self.app = flask_app
        self.load_user_session = load_user_session
        self.login_manager = login_manager

    def register(self):
        self.app.add_url_rule('/', view_func=self.__index(), methods=['GET', 'POST'], endpoint='')
        self.app.add_url_rule('/index', view_func=self.__index(), methods=['GET', 'POST'], endpoint='index')
        self.app.add_url_rule('/logout', view_func=self.__logout())
        self.app.add_url_rule('/sessions/info/offline/<int:session_id>', view_func=self.__sessions_info_offline())
        self.app.add_url_rule(
            '/sessions/info/online/<int:session_id>', view_func=self.__sessions_turn_online(), methods=['GET', 'POST'])
        self.app.add_url_rule(
            '/sessions/edit/<int:session_id>', view_func=self.__sessions_edit(), methods=['GET', 'POST'])
        self.app.add_url_rule('/sessions/delete/<int:session_id>', view_func=self.__sessions_delete())
        self.app.add_url_rule(
            '/sessions/add', view_func=self.__sessions_add(self.load_user_session), methods=['GET', 'POST'])
        self.app.add_url_rule('/register', view_func=self.__register(), methods=['GET', 'POST'], endpoint='register1')
        self.app.add_url_rule('/register/', view_func=self.__register(), methods=['GET', 'POST'], endpoint='register2')
        self.app.add_url_rule('/signin', view_func=self.__signin(), methods=['GET', 'POST'])
        self.app.add_url_rule(
            '/profile/<int:user_id>', view_func=self.__profile(self.load_user_session), methods=['GET', 'POST'])
        self.app.add_url_rule('/help_project', view_func=self.__help_project(), methods=['GET', 'POST'])
        self.app.add_url_rule(
            '/help_project/<bill_id>/<invoice_uid>', view_func=self.__help_project_check(), methods=['GET', 'POST'])
        # добавление правила для доступа к сохранениям
        self.app.add_url_rule(
            f'/all_savings/<path:filename>', endpoint='all_savings', view_func=self.__all_savings_url_rule(self.app))
        # установка метода получения пользователей
        self.login_manager.user_loader(self.__load_user())

    # метод для получения файлов из корневой папки source_code
    @staticmethod
    def __all_savings_url_rule(app):
        def all_savings_url_rule(filename):
            value = app.send_file_max_age_default
            if value is None:
                max_age = None
            else:
                max_age = int(value.total_seconds())
            filename = filename.replace('\\', '/')
            return send_from_directory('db/all_savings', filename, max_age=max_age)
        return all_savings_url_rule

    @staticmethod
    def __index():
        def index():
            db_sess = db_session.create_session()
            sessions = db_sess.query(Sessions)
            sessions_ids = [session.session_id for session in sessions]
            if request.method == 'POST':
                if current_user.is_authenticated:
                    # проверка, есть ли пользователь на главном дискорд сервере
                    is_guilder = get_discord_session().is_guilder(current_user.discord)
                    if not is_guilder:
                        flask.flash(NOT_GUILDER_ERROR['error'], category='error')
                    # получение тега name у file_input`ов, id сессий которых ЕСТЬ в активных сессиях
                    names = [elem for elem in request.files
                             if elem.startswith('load_saving_inp_') and elem[len('load_saving_inp_'):].isdigit()
                             and int(elem[len('load_saving_inp_'):]) in sessions_ids]
                    for name in names:
                        session_id = int(name[len('load_saving_inp_'):])
                        session = sessions.filter(Sessions.session_id == session_id).first()
                        if session.is_online and session.last_opener_id != current_user.id:
                            db_sess.close()
                            return render_template('error.html', **NOT_ALLOWED)
                        # сохраняем файл как ненужное
                        file = request.files[name]
                        saving_path = generate_filename('source_code/db/trash/adding_sessions/savings', '.sav')
                        file.save(saving_path)
                        # проверка на правильность сохранения
                        sav_parser1 = SatisfactorySaveParser(session.savings[-1].saving_path)
                        sav_parser2 = SatisfactorySaveParser(saving_path)
                        if not sav_parser2.is_correct_save():
                            flask.flash('Sav file is incorrect', category='error')
                            break
                        if not sav_parser1.is_next_save(saving_path):
                            flask.flash(
                                'Seems like you were not playing on this save or save is not the next after current',
                                category='error')
                            break
                        # если всё нормально, то перемещаем его
                        new_saving_path = generate_filename('source_code/db/all_savings/savings', '.sav')
                        shutil.move(saving_path, new_saving_path)
                        # добавляем сессию в активные
                        saving = Savings(owner_id=current_user.id, saving_path=new_saving_path)
                        db_sess.add(saving)
                        db_sess.commit()

                        session.savings.append(saving)
                        db_sess.commit()

                        flask.flash('Saving was successfully loaded', category='success')
                else:
                    flask.flash(UNAUTHORIZED_ERROR['error'], category='error')
            db_sess.close()
            return render_template('index.html', sessions=sessions)
        return index

    def __load_user(self):
        def load_user(user_id):
            return self.load_user_session.query(Users).filter(Users.id == user_id).first()
        return load_user

    @staticmethod
    def __logout():
        @login_required
        def logout():
            logout_user()
            return flask.redirect("/")
        return logout

    # перевод сессии в оффлайн
    @staticmethod
    def __sessions_info_offline():
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
        return sessions_info_offline

    # перевод сессии в онлайн
    @staticmethod
    def __sessions_turn_online():
        @login_required
        def sessions_info_online(session_id):
            db_sess = db_session.create_session()
            # проверка, есть ли пользователь на главном дискорд сервере
            is_guilder = get_discord_session().is_guilder(current_user.discord)
            if not is_guilder:
                db_sess.close()
                return render_template('error.html', **NOT_GUILDER_ERROR)
            session = db_sess.query(Sessions).filter(Sessions.session_id == session_id).first()
            if session.is_online:
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
            return render_template('sessions_turn_online.html', form=form)
        return sessions_info_online

    # скрыть/удалить сессию
    @staticmethod
    def __sessions_delete():
        @login_required
        def sessions_delete(session_id):
            db_sess = db_session.create_session()
            is_guilder = get_discord_session().is_guilder(current_user.discord)
            session = db_sess.query(Sessions).filter(Sessions.session_id == session_id).first()
            # проверка, существует ли сессия и является ли пользователь владельцем сессии
            if session is None or not session.is_active or session.creator_id != current_user.id:
                db_sess.close()
                return render_template('error.html', **NOT_ALLOWED)
            # проверка, есть ли пользователь на главном дискорд сервере
            if not is_guilder:
                db_sess.close()
                return render_template('error.html', **NOT_GUILDER_ERROR)
            session.is_active = False
            db_sess.commit()
            db_sess.close()
            return redirect('/')
        return sessions_delete

    @staticmethod
    def __sessions_edit():
        @login_required
        def sessions_edit(session_id):
            if not any([session.session_id == session_id for session in current_user.sessions]):
                return render_template('error.html', **NOT_ALLOWED)
            changing = request.args.get('changing', default=None, type=str)
            # проверка, есть ли пользователь на главном дискорд сервере
            is_guilder = get_discord_session().is_guilder(current_user.discord)
            if not is_guilder:
                return render_template('error.html', **NOT_GUILDER_ERROR)
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
        return sessions_edit

    @staticmethod
    def __sessions_add(load_user_session: Session):
        @login_required
        def sessions_add():
            if not any([privilege.key_name == 'session_creator' for privilege in current_user.privileges]):
                return render_template('error.html', **NOT_ALLOWED)
            form = SessionsAddForm()
            if form.validate_on_submit():
                # сохранение всего как ненужное для промежуточного анализа
                saving_path = generate_filename('source_code/db/trash/adding_sessions/savings', '.sav')
                form.saving.data.save(saving_path)
                photo_path_secured = secure_filename(form.session_photo.data.filename)
                photo_path = generate_filename('source_code/db/trash/adding_sessions/photos', f'{photo_path_secured}')
                form.session_photo.data.save(photo_path)
                # проверка на правильность сохранения
                sav_parser = SatisfactorySaveParser(saving_path)
                if not sav_parser.is_correct_save():
                    form.saving.errors.append('Sav file is incorrect')
                    return render_template('sessions_add.html', form=form)
                db_sess = db_session.create_session()
                session_id = max([elem.session_id for elem in db_sess.query(Sessions)]) + 1
                # преведение sav_parser к базовым настрйокам
                sav_parser.reset(session_id)
                sav_parser.save(saving_path)
                # если всё нормально, то перемещаем их
                new_saving_path = generate_filename('source_code/db/all_savings/savings', '.sav')
                shutil.move(saving_path, new_saving_path)
                new_photo_path = generate_filename('source_code/db/all_savings/photos', f'{photo_path_secured}')
                shutil.move(photo_path, new_photo_path)
                # добавляем сессию в активные
                saving = Savings(owner_id=current_user.id, saving_path=new_saving_path)
                db_sess.add(saving)
                db_sess.commit()
                session = Sessions(session_id=session_id, creator_id=current_user.id,
                                   description=form.session_description.data,
                                   photo_path=new_photo_path, name=form.session_name.data,
                                   is_active=True, is_online=False)
                session.savings.append(saving)
                db_sess.add(session)
                db_sess.commit()
                db_sess.close()
                current_user.sessions.append(session)
                load_user_session.commit()
                return redirect('/')
            return render_template('sessions_add.html', form=form)
        return sessions_add

    @staticmethod
    def __register():
        def register():
            form = RegisterForm()
            if form.validate_on_submit():
                db_sess = db_session.create_session()
                if db_sess.query(Users).filter(Users.login == form.login.data).first():
                    return render_template('register.html', form=form, modal_message="Such user already exists")
                user = Users(login=form.login.data, discord=form.discord.data)
                user.set_password(form.password.data)
                db_sess.add(user)
                db_sess.commit()
                login_user(user, remember=form.remember_me.data)
                db_sess.close()
                return redirect("/")
            return render_template('register.html', form=form)
        return register

    # профиль пользователя
    @staticmethod
    def __profile(load_user_session: Session):
        def profile(user_id):
            db_sess = db_session.create_session()
            user = db_sess.query(Users).filter(Users.id == user_id).first()
            form = ProfileForm(user.login, user.discord)
            db_sess.close()
            if user is None:
                return render_template('error.html', **NOT_FOUND)
            if form.validate_on_submit():
                if not current_user.is_authenticated or current_user.id != user_id:
                    return render_template('error.html', **NOT_ALLOWED)
                current_user.login = form.login.data
                current_user.discord = form.discord.data
                load_user_session.commit()
            return render_template('profile.html', user=user, form=form)
        return profile

    @staticmethod
    def __signin():
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
                    user = db_sess.query(Users).filter(Users.discord == form.discord.data).first()
                    login_user(user, remember=form.discord_remember_me.data)
                    return redirect("/")
            return render_template('signin.html', form=form)
        return signin

    # помощь проекту с выбором цены оплаты
    @staticmethod
    def __help_project():
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
        return help_project

    # проверка платежа помощи проекту
    @staticmethod
    def __help_project_check():
        def help_project_check(bill_id, invoice_uid):
            if request.method == 'POST':
                if 'check' not in request.form:
                    return render_template(
                        'help_project.html', action='check',
                        payload=f'https://oplata.qiwi.com/form/?invoice_uid={invoice_uid}',
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
                            payload_message += '. You will get the role in discord in one minute.'
                return render_template(
                    'help_project.html', action='check',
                    payload=f'https://oplata.qiwi.com/form/?invoice_uid={invoice_uid}',
                    payload_message=payload_message, not_load_help_project_footer=True)
            else:
                return render_template(
                    'help_project.html', action='check',
                    payload=f'https://oplata.qiwi.com/form/?invoice_uid={invoice_uid}',
                    not_load_help_project_footer=True)
        return help_project_check
