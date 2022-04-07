import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Sessions(SqlAlchemyBase):
    __tablename__ = 'sessions'

    session_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    saving_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("all_savings.saving_id"), nullable=True)

    saving = orm.relation('Savings')
