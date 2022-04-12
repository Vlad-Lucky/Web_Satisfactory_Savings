import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


sessions2savings = sqlalchemy.Table(
    'sessions2savings',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('sessions', sqlalchemy.Integer, sqlalchemy.ForeignKey('sessions.session_id')),
    sqlalchemy.Column('savings', sqlalchemy.Integer, sqlalchemy.ForeignKey('savings.saving_id'))
)


class Savings(SqlAlchemyBase):
    __tablename__ = 'savings'

    saving_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    # владелец сохранения
    owner_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    saving_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    upload_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    owner = orm.relation("Users")
