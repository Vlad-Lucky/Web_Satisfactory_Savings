import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


users2sessions = sqlalchemy.Table(
    'users2sessions',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('users', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('sessions', sqlalchemy.Integer, sqlalchemy.ForeignKey('sessions.session_id'))
)


class Sessions(SqlAlchemyBase):
    __tablename__ = 'sessions'

    session_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    saving_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("savings.saving_id"), nullable=True)
    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)

    saving = orm.relation('Savings')
    creator = orm.relation('Users')
