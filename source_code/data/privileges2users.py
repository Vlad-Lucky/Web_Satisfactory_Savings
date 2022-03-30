import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Privileges2Users(SqlAlchemyBase):
    __tablename__ = 'privileges2users'

    privilege_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("privileges.privilege_id"),
                                     primary_key=True, nullable=True)
    privilege = orm.relation("Privileges")

    user_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("users.user_id"))
    user = orm.relation("Users")
