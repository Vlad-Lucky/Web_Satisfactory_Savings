import sqlalchemy
from .db_session import SqlAlchemyBase


class Privileges(SqlAlchemyBase):
    __tablename__ = 'privileges'

    privilege_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_displaying = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
