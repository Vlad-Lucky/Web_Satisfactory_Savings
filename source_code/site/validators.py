from werkzeug.utils import secure_filename
from wtforms import ValidationError
from source_code.data import db_session
from source_code.data.users import Users


# проверка sav файла на правильность содержания заголовков
def correct_sav_headers_validator(form, field):
    try:
        filename = secure_filename(field.data.filename)
        form.file.data.save('source_code/db/trash/' + filename)
    except Exception:
        raise ValidationError("File .sav is incorrect")


# проверка зарегестрированного пользователя по логину
def signin_login_validator(form, field):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.login == form.login.data).first()
    if not user or not user.check_password(form.login_password.data):
        raise ValidationError("Login or password is incorrect")


# проверка зарегестрированного пользователя по дискорду
def signin_discord_validator(form, field):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.discord == form.discord_login.data).first()
    if not user or not user.check_password(form.discord_password.data):
        raise ValidationError("Login or password is incorrect")


# проверка зарегестрированного пользователя по логину и дискорду. Если есть что-то одно, то ошибки нет
def signin_validator(form, field):
    signin_login_validators = [signin_login_validator]
    signin_discord_validators = [signin_discord_validator]

    signin_login = True
    signin_discord = True

    for validator in signin_login_validators:
        try:
            validator(form, None)
        except ValidationError:
            signin_login = False
    for validator in signin_discord_validators:
        try:
            validator(form, None)
        except ValidationError:
            signin_discord = False
    if (not signin_login and not signin_discord) or \
            (not signin_login and form.login_submit.data and field is form.login_password) or\
            (not signin_discord and form.discord_submit.data and field is form.discord_password):
        raise ValidationError("Login or password is incorrect")


# проверка, зарегестрирован ли уже логин
def registration_login_validator(form, field):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.login == field.data).first()
    if user:
        raise ValidationError("Such login already exists")


# проверка discord ника на правильность и на то, существует ли он уже
def registration_discord_validator(form, field):
    try:
        if field.data.count('#') != 1 or len(field.data.split('#')[-1]) != 4:
            raise ValueError
        int(field.data.split('#')[-1])
    except ValueError:
        raise ValidationError("Discord login is incorrect")

    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.discord == field.data).first()
    if user:
        raise ValidationError("Such user already exists")


# проверка на repeat_password
def registration_password_equal_validator(form, field):
    if form.password.data != form.repeat_password.data:
        raise ValidationError("Passwords are not equal")
