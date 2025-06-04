from pathlib import Path
import configparser
import os

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = os.path.join(BASE_DIR, 'settings.ini')

config = configparser.ConfigParser()

# Читаем файл settings.ini
try:
    config.read(CONFIG_PATH)
except configparser.Error as e:
    print(f"Ошибка при чтении файла settings.ini: {e}")
    exit()

try:
    DB_NAME = config['MySQL Database']['name']
    DB_USER = config['MySQL Database']['user']
    DB_PASSWORD = config['MySQL Database']['password']
    DB_HOST = config['MySQL Database']['host']
    DB_PORT = config['MySQL Database']['port']
    PAGE_SIZE = config['Other']['page_size']
except KeyError as e:
    print(f"Отсутствует ключ в секции 'MySQL Database' в settings.ini: {e}")
    exit()
except ValueError as e:
    print(f"Ошибка преобразования типа в settings.ini: {e}")
    exit()

SECRET_KEY = 'django-insecure-sups03ym0_5&b5=*$#0!0462xc*@6jvl=3t+dhxc*p6ar_3zmp'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'equipment',
    'django_filters',
]

CORS_ALLOW_ALL_ORIGINS = True 

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': PAGE_SIZE,

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', # По умолчанию все эндпоинты требуют аутентификации
    ),

    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],

}

# Настройки Simple JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # Время жизни access токена
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # Время жизни refresh токена
    'ROTATE_REFRESH_TOKENS': False, # Если True, при каждом обновлении будет выдаваться новый refresh токен
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True, # Обновлять last_login пользователя при логине

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY, # Использует SECRET_KEY из Django настроек
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',), # Тип заголовка авторизации (Bearer <token>)
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}