import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Privileges2Bills(SqlAlchemyBase):
    __tablename__ = 'privileges2bills'

    privilege_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("privileges.privilege_id"),
                                     primary_key=True, nullable=True)
    privilege = orm.relation("Privileges")

    bill_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("bills.bill_id"))
    bill = orm.relation("Bills")
