import datetime as dt
from source_code.data import db_session
from source_code.data.bills import Bills
from source_code.data.privileges import Privileges
from source_code.constants import QIWI_TIME_TO_PAY, PRIVILEGES
from source_code.misc.generating_ids import check_uniqueness_bill_id, generate_uniqueness_bill_id
from source_code.misc.payment import make_session, unconvert_from_payment_dt


# генерация платежа для помощи проекту
def generate_help_project_payload(amount: int, for_user_id: float = None) -> dict:
    session = make_session()
    bill_id = generate_uniqueness_bill_id(session)

    if for_user_id is not None:
        db_sess = db_session.create_session()

        # удаляем данные о прошлой оплате
        bill = db_sess.query(Bills).filter(Bills.user_id == for_user_id)
        contributor_privilege = db_sess.query(Privileges).filter(Privileges.key_name == 'contributor').first()
        if any(bill):
            if check_uniqueness_bill_id(bill.one().bill_id, session):
                session.post(f'https://api.qiwi.com/partner/bill/v1/bills/{bill.one().bill_id}/reject')
            contributor_privilege.bills.remove(bill)
            bill.delete()

        # сохранение bill_id как последнюю оплату, которую пользователь запрашивал
        bill = Bills()
        bill.bill_id = bill_id
        bill.is_active = True
        bill.user_id = for_user_id

        db_sess.add(bill)
        contributor_privilege.bills.append(bill)

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
