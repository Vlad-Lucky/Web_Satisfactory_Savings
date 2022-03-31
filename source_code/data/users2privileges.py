import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Users2Privileges(SqlAlchemyBase):
    __tablename__ = 'users2privileges'

    user_id = sqlalchemy.Column(
        sqlalchemy.String, sqlalchemy.ForeignKey("users.id"), primary_key=True, nullable=True)
    user = orm.relation("Users")

    privilege_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("privileges.privilege_id"), nullable=True)
    privilege = orm.relation("Privileges")
