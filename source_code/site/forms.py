from flask_login import login_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, EmailField, IntegerField
from wtforms.validators import DataRequired, ValidationError
from source_code.data import db_session
from source_code.data.users import Users


def signin_login_validator(form, field):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.login == form.login.data).first()
    if not user or not user.check_password(form.login_password.data):
        raise ValidationError("Login or password is incorrect")


def signin_discord_validator(form, field):
    db_sess = db_session.create_session()
    user = db_sess.query(Users).filter(Users.discord == form.discord_login.data).first()
    if not user or not user.check_password(form.discord_password.data):
        raise ValidationError("Login or password is incorrect")


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


def registration_discord_validator(form, field):
    try:
        if field.data.count('#') != 1 or len(field.data.split('#')[-1]) != 4:
            raise ValueError
        int(field.data.split('#')[-1])
    except ValueError:
        raise ValidationError("Discord login is incorrect")


def registration_password_equal_validator(form, field):
    if form.password.data != form.repeat_password.data:
        raise ValidationError("Passwords are not equal")


class SigninForm(FlaskForm):
    login = StringField('Login')
    login_password = PasswordField('Password', validators=[signin_validator])
    login_remember_me = BooleanField('Remember me')
    login_submit = SubmitField('Sign in')

    discord_login = StringField('<discord_name>#<tag>')
    discord_password = PasswordField('Password', validators=[signin_validator])
    discord_remember_me = BooleanField('Remember me')
    discord_submit = SubmitField('Sign in')


class RegisterForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    discord_login = StringField('<discord_name>#<tag>', validators=[DataRequired(), registration_discord_validator])
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat password',
                                    validators=[DataRequired(), registration_password_equal_validator])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Register')
