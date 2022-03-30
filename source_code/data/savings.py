import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Savings(SqlAlchemyBase):
    __tablename__ = 'savings'

    saving_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.user_id"), nullable=True)
    saving_file = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    info = sqlalchemy.Column(sqlalchemy.JSON, nullable=True)
    upload_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    owner = orm.relation("Users")
