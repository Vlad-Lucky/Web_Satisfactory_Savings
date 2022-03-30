import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Users(SqlAlchemyBase):
    __tablename__ = 'users'

    user_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    discord = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    saving_rights = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
