from wtforms import ValidationError
from source_code.data import db_session
from source_code.data.users import Users


# проверка всех условий, передаются условия так:
# [[<элемент в форме в str>, <значение, при котором вызываются валидатор>,
# [<методы-валидаторы, получаемые параметры (form, field)>, ...]], [...]...]
def conditions_required(conditions):
    def cmd(form, field):
        for condition in conditions:
            value = form.data.get(condition[0])
            if value != condition[1]:
                continue
            for validator in condition[2]:
                validator(form, field)
    return cmd


# проверка всех условий, передаются условия так:
# [[<валидатор при значениях (form, field), если он завершается без ошибки ValidationError при котором
# вызываются последующие валидатор>, [<методы-валидаторы, получаемые параметры (form, field)>, ...]],[...]...]
def validator_conditions_required(conditions):
    def cmd(form, field):
        for condition in conditions:
            try:
                condition[0](form, field)
            except ValidationError:
                continue
            for validator in condition[1]:
                validator(form, field)
    return cmd


# проверка на то, что значение поля НЕ соответствует перечисленному
def except_values_validator(except_values: list):
    def cmd(form, field):
        if field.data in except_values:
            raise ValidationError("Field value is incorrect")
    return cmd


# проверка зарегестрированного пользователя по логину
def signin_login_validator():
    def cmd(form, field):
        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.login == form.login.data).first()
        if not user or not user.check_password(form.login_password.data):
            raise ValidationError("Login or password is incorrect")
    return cmd


# проверка зарегестрированного пользователя по дискорду
def signin_discord_validator():
    def cmd(form, field):
        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.discord == form.discord.data).first()
        if not user or not user.check_password(form.discord_password.data):
            raise ValidationError("Login or password is incorrect")
    return cmd


# проверка зарегестрированного пользователя по логину и дискорду. Если есть что-то одно, то ошибки нет
def signin_validator():
    def cmd(form, field):
        signin_login_validators = [signin_login_validator()]
        signin_discord_validators = [signin_discord_validator()]

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
            raise ValidationError("Login or discord or password is incorrect")
    return cmd


# проверка, зарегестрирован ли уже логин
def login_validator():
    def cmd(form, field):
        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.login == field.data).first()
        if user:
            raise ValidationError("Such login already exists")
    return cmd


# проверка discord ника на правильность и на то, существует ли он уже
def discord_validator():
    def cmd(form, field):
        try:
            if field.data.count('#') != 1 or len(field.data.split('#')[-1]) != 4:
                raise ValueError
            int(field.data.split('#')[-1])
        except ValueError:
            raise ValidationError("Discord login is incorrect")

        db_sess = db_session.create_session()
        user = db_sess.query(Users).filter(Users.discord == field.data).first()
        if user:
            raise ValidationError("Such discord is already registered")
    return cmd


# проверка на repeat_password
def password_equal_validator():
    def cmd(form, field):
        if form.password.data != form.repeat_password.data:
            raise ValidationError("Passwords are not equal")
    return cmd
