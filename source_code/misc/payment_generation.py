import datetime as dt
from source_code.data import db_session
from source_code.data.bills import Bills
from source_code.data.privileges import Privileges
from source_code.constants import QIWI_TIME_TO_PAY, PRIVILEGES
from source_code.data.priveleges2bills import Privileges2Bills
from source_code.misc.payment import make_session, unconvert_from_payment_dt, check_uniqueness_bill_id, \
    generate_uniqueness_bill_id


# генерация платежа для помощи проекту
def generate_help_project_payload(amount: int, for_user_id: float = None) -> dict:
    session = make_session()
    bill_id = generate_uniqueness_bill_id(session)

    if for_user_id is not None:
        db_sess = db_session.create_session()

        privilege_id = db_sess.query(Privileges).filter(
            Privileges.privilege_id == PRIVILEGES['contributor']).one().privilege_id

        # удаляем данные о прошлой оплате
        bill = db_sess.query(Bills).filter(Bills.user_id == for_user_id)
        if any(bill):
            if check_uniqueness_bill_id(bill.one().bill_id, session):
                session.post(f'https://api.qiwi.com/partner/bill/v1/bills/{bill.one().bill_id}/reject')
            bill.delete()
        privilege2bill = db_sess.query(Privileges2Bills).filter(Privileges2Bills.privilege_id == privilege_id)
        if any(privilege2bill):
            privilege2bill.delete()

        # сохранение bill_id как последнюю оплату, которую пользователь запрашивал
        bill = Bills()
        bill.bill_id = bill_id
        bill.is_active = True
        bill.user_id = for_user_id
        db_sess.add(bill)

        privilege2bill = Privileges2Bills()
        privilege2bill.bill_id = bill_id
        privilege2bill.privilege_id = privilege_id
        db_sess.add(privilege2bill)

        db_sess.commit()

    # создание ссылки-оплаты
    payload = f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}'
    data_row = {
        "amount": {
            "currency": "RUB",
            "value": f"{amount}.00"
        },
        "comment": "Satisfactory Saver",
        "expirationDateTime": f"{unconvert_from_payment_dt((dt.datetime.now() + QIWI_TIME_TO_PAY))}",
        "customFields": {
            "paySourcesFilter": "qw,card"
        }
    }
    payload = session.put(payload, json=data_row).json()

    return payload
