import rsa
import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from .db_session import SqlAlchemyBase
from ..constants import PASSWORDS_CIPHER_PRIVATE, PASSWORDS_CIPHER_PUBLIC


class Users(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    discord = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    saving_rights = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    hashed_password = sqlalchemy.Column(sqlalchemy.LargeBinary, nullable=True)

    privileges = orm.relation("Privileges", secondary="users2privileges", backref="users")
    sessions = orm.relation("Sessions", secondary="users2sessions", backref="users")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hashed_password = None

    def set_password(self, password: str):
        self.hashed_password = rsa.encrypt(password.encode('utf-8'), PASSWORDS_CIPHER_PUBLIC)

    def check_password(self, password: str):
        decrypted = rsa.decrypt(self.hashed_password, PASSWORDS_CIPHER_PRIVATE).decode('utf-8')
        return decrypted == password
