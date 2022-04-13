import os
import random
import requests
from source_code.constants import FILE_ID_AVAILABLE_SYMBOLS, FILE_ID_MAX_LEN, QIWI_PAYMENT_AVAILABLE_SYMBOLS, \
    QIWI_MAX_LEN_PAYMENT_LINK


# генерация файла с уникальным id
def generate_filename(folder: str, base_filename: str = None):
    if base_filename is None:
        base_filename = ''
    file_id = None
    if not os.path.exists(folder):
        os.makedirs(folder)
    while file_id is None or f'{file_id}_{base_filename}' in os.listdir(folder):
        file_id = ''
        for _ in range(random.randint(1, FILE_ID_MAX_LEN)):
            file_id += random.choice(FILE_ID_AVAILABLE_SYMBOLS)
    return os.path.join(folder, f'{file_id}{base_filename}')


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
