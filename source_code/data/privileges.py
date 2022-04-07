import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


users2privileges = sqlalchemy.Table(
    'users2privileges',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('users', sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id')),
    sqlalchemy.Column('privileges', sqlalchemy.Integer, sqlalchemy.ForeignKey('privileges.privilege_id'))
)


class Privileges(SqlAlchemyBase):
    __tablename__ = 'privileges'

    privilege_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    key_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_displaying = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    bills = orm.relation("Bills", secondary="privileges2bills", backref="privileges")
