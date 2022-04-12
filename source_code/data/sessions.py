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
    # создатель сессии
    creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    # тот, кто открыл сессию в онлайне
    last_opener_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    photo_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_online = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)

    creator = orm.relation('Users', primaryjoin='Sessions.creator_id == Users.id')
    last_opener = orm.relation('Users', primaryjoin='Sessions.last_opener_id == Users.id')
    savings = orm.relation("Savings", secondary="sessions2savings", backref="sessions")
