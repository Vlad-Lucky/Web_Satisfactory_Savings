import random
import requests
import datetime as dt
from enum import Enum
from source_code.constants import QIWI_MAX_LEN_PAYMENT_LINK, QIWI_PAYMENT_AVAILABLE_SYMBOLS, QIWI_SECRET_KEY


class PaymentStatus(Enum):
    WAITING = 'WAITING'
    PAID = 'PAID'
    REJECTED = 'REJECTED'
    EXPIRED = 'EXPIRED'


# создаёт сессию для bill_id
def make_session() -> requests.Session:
    req = requests.Session()
    req.headers['accept'] = 'application/json'
    req.headers['Content-Type'] = 'application/json'
    req.headers['Authorization'] = f'Bearer {QIWI_SECRET_KEY}'
    return req


# генерирует bill_id
def generate_bill_id() -> str:
    bill_id = ''
    for _ in range(random.randint(1, QIWI_MAX_LEN_PAYMENT_LINK)):
        bill_id += random.choice(QIWI_PAYMENT_AVAILABLE_SYMBOLS)
    return bill_id


# проверяет bill_id на уникальность
def check_uniqueness_bill_id(bill_id: str, session: requests.Session) -> bool:
    return session.get(f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}'). \
               json().get('errorCode', None) == 'api.invoice.not.found'


# генерация уникального bill_id
def generate_uniqueness_bill_id(session: requests.Session) -> str:
    bill_id = generate_bill_id()
    while not check_uniqueness_bill_id(bill_id, session):
        bill_id = generate_bill_id()
    return bill_id


# конвертирует строку в формат datetime, использующийся в lifetime платеже
def convert_to_payment_dt(datetime_str: str) -> dt.datetime:
    return dt.datetime.strptime(datetime_str, '%Y-%m-%dT%H%M')


# преобразование datetime, использующийся в lifetime платеже, в строку
def unconvert_from_payment_dt(datetime: dt.datetime) -> str:
    return datetime.strftime('%Y-%m-%dT%H:%M:%S+03:00')
