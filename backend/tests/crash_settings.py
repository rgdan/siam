import os

from config.settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ["SIAM_CRASH_DB"],
        "OPTIONS": {"transaction_mode": "IMMEDIATE"},
    }
}
ROOT_URLCONF = "tests.crash_urls"
