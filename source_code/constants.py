import datetime as dt


QIWI_MAX_LEN_PAYMENT_LINK = 100
QIWI_PAYMENT_AVAILABLE_SYMBOLS = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM-_'
QIWI_PUBLIC_KEY = '<Qiwi public key>'
QIWI_SECRET_KEY = '<Qiwi secret key>'
QIWI_TIME_TO_PAY = dt.timedelta(minutes=5)

# short_name: privilege_id
PRIVILEGES = {'contributor': 1}

SITE_URL = 'http://127.0.0.1:8080/'
