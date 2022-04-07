import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Savings(SqlAlchemyBase):
    __tablename__ = 'savings'

    saving_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    saving_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    upload_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    owner = orm.relation("Users")
