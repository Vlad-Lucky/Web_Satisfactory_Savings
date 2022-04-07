import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash


class Users(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    discord = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    saving_rights = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    privileges = orm.relation("Privileges", secondary="users2privileges", backref="users")
    sessions = orm.relation("Sessions", secondary="users2sessions", backref="users")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hashed_password = None

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
