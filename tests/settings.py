import os

from django.utils.translation import gettext_lazy

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# These overly specific paths are for jinja2
TEMPLATE_DIRS = [
    os.path.join(BASE_DIR, 'tests'),
]

TEMPLATE_DEBUG = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': TEMPLATE_DEBUG,
        },
    },
]

SECRET_KEY = "foobar"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': 'okrand.sqlite',
        'NAME': ':memory:',
    }
}

USE_TZ = False

LANGUAGES = [
    ('sv', gettext_lazy('Swedish')),
    ('en', gettext_lazy('English')),
    ('tlh', gettext_lazy('Klingon')),
]


PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'iommi',
    'okrand',
    'tests',
]

ROOT_URLCONF = 'tests.urls'

DATETIME_FORMAT = r'\d\a\t\e\t\i\m\e\: N j, Y, P'
DATE_FORMAT = r'\d\a\t\e\: N j, Y'
TIME_FORMAT = r'\t\i\m\e\: P'
