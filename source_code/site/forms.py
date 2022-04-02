from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, Length
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField
from source_code.site.validators import signin_validator, registration_discord_validator, \
    registration_password_equal_validator, registration_login_validator, correct_sav_headers_validator


class SessionAddForm(FlaskForm):
    session_name = StringField('Session name', validators=[DataRequired(), Length(min=1, max=24)])
    session_description = StringField('Session description', validators=[DataRequired(), Length(min=0, max=192)])
    saving = FileField("Saving", validators=[DataRequired(), FileAllowed(['sav']), correct_sav_headers_validator])
    photo = FileField("Photo", validators=[DataRequired(),
                                           FileAllowed(['jpg', 'jpeg', 'png', 'bmp', 'JPG', 'JPEG', 'PNG', 'BMP'])])
    submit = SubmitField('Submit')


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
    login = StringField('Login', validators=[DataRequired(), registration_login_validator])
    discord_login = StringField('<discord_name>#<tag>', validators=[DataRequired(), registration_discord_validator])
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat password',
                                    validators=[DataRequired(), registration_password_equal_validator])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Register')
