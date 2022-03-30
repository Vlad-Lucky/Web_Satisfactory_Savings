import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Bills(SqlAlchemyBase):
    __tablename__ = 'bills'

    bill_id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.user_id"), nullable=True)

    user = orm.relation("Users")
