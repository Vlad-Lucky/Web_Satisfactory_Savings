import requests
import datetime as dt
from enum import Enum
from source_code.constants import QIWI_SECRET_KEY


class QiwiPaymentStatus(Enum):
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


# конвертирует строку в формат datetime, использующийся в lifetime платеже
def convert_to_payment_dt(datetime_str: str) -> dt.datetime:
    return dt.datetime.strptime(datetime_str, '%Y-%m-%dT%H%M')


# преобразование datetime, использующийся в lifetime платеже, в строку
def unconvert_from_payment_dt(datetime: dt.datetime) -> str:
    return datetime.strftime('%Y-%m-%dT%H:%M:%S+03:00')
