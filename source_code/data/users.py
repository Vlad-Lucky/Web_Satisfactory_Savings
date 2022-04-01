import datetime
import sqlalchemy
from . import db_session
from flask_login import UserMixin
from .db_session import SqlAlchemyBase
from .users2privileges import Users2Privileges
from werkzeug.security import generate_password_hash, check_password_hash


class Users(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    discord = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    saving_rights = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hashed_password = None

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    @property
    def privileges(self) -> list:
        session = db_session.create_session()
        res = session.query(Users2Privileges).filter(Users2Privileges.user_id == 1)
        res = [elem.privilege for elem in res]
        return list(res)
