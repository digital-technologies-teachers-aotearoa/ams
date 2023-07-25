from os import environ
from pathlib import Path
from typing import Iterable, Optional

import sentry_sdk
from configurations import Configuration
from sentry_sdk.integrations.django import DjangoIntegration


class Common(Configuration):
    @classmethod
    def setup(cls) -> None:
        super().setup()

        dsn: Optional[str] = environ.get("SENTRY_DSN")
        if dsn == "":
            dsn = None
        sentry_sdk.init(
            dsn=dsn,
            release=environ.get("APPLICATION_VERSION"),
            server_name=environ["APPLICATION_WEB_HOST"],
            integrations=[DjangoIntegration()],
            send_default_pii=True,
        )

    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent

    # SECURITY WARNING: don't run with debug turned on in production!
    SECRET_KEY = environ["DJANGO_SECRET_KEY"]

    DEBUG = False

    ALLOWED_HOSTS: Iterable[str] = ["backend", environ["APPLICATION_WEB_HOST"]]

    # Application definition

    INSTALLED_APPS = [
        "ams.base",
        "ams.users",
        "ams.dtta",
        "registration",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "wagtail.contrib.forms",
        "wagtail.contrib.redirects",
        "wagtail.contrib.simple_translation",
        "wagtail.contrib.modeladmin",
        "wagtailmenus",
        "wagtail.embeds",
        "wagtail.sites",
        "wagtail.users",
        "wagtail.snippets",
        "wagtail.documents",
        "wagtail.images",
        "wagtail.search",
        "wagtail.admin",
        "wagtail.locales",
        "wagtail",
        "modelcluster",
        "taggit",
        "django_tables2",
    ]

    MIDDLEWARE = [
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    ]

    ROOT_URLCONF = "ams.urls"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "wagtailmenus.context_processors.wagtailmenus",
                ],
            },
        },
    ]

    WSGI_APPLICATION = "ams.wsgi.application"

    # Database
    # https://docs.djangoproject.com/en/4.2/ref/settings/#databases

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": environ["APPLICATION_DB_NAME"],
            "USER": environ["APPLICATION_DB_USER"],
            "HOST": environ["APPLICATION_DB_HOST"],
            "PASSWORD": environ["APPLICATION_DB_PASSWORD"],
            "PORT": 5432,
            "OPTIONS": {"connect_timeout": 5},
            "ATOMIC_REQUESTS": True,
        }
    }

    # Password validation
    # https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/4.2/topics/i18n/

    LANGUAGE_CODE = "en"

    TIME_ZONE = "Pacific/Auckland"

    USE_I18N = True

    USE_TZ = True

    SHORT_DATE_FORMAT = "d/m/Y"

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/4.2/howto/static-files/
    # TODO: probably should serve static files from Nginx

    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / "static"

    # User uploaded files
    # https://docs.djangoproject.com/en/4.2/topics/files/
    # TODO: need solution production solution for user uploaded files

    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"

    # Email
    # https://docs.djangoproject.com/en/4.2/topics/email/

    EMAIL_HOST = environ["EMAIL_HOST"]
    EMAIL_HOST_USER = environ["EMAIL_HOST_USER"]
    EMAIL_HOST_PASSWORD = environ["EMAIL_HOST_PASSWORD"]

    # Wagtail settings
    # https://docs.wagtail.org/en/stable/reference/settings.html

    WAGTAIL_SITE_NAME = "DTTA - Association Management Software"
    WAGTAILADMIN_BASE_URL = environ["APPLICATION_WEB_HOST"] + "/cms"
    WAGTAIL_I18N_ENABLED = True
    WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
        ("en", "English"),
        ("mi", "Maori"),
    ]
    WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE = False

    # Django registration redux
    # https://django-registration-redux.readthedocs.io/en/latest/quickstart.html

    ACCOUNT_ACTIVATION_DAYS = 7
    REGISTRATION_AUTO_LOGIN = False
    REGISTRATION_EMAIL_HTML = False
    LOGIN_REDIRECT_URL = "/"
    LOGOUT_REDIRECT_URL = "/"

    # Default primary key field type
    # https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


class Development(Common):
    DEBUG = True
    CSRF_TRUSTED_ORIGINS = ["http://" + environ["APPLICATION_WEB_HOST"] + ":1800"]


class Testing(Common):
    DEBUG = False
    CSRF_TRUSTED_ORIGINS = ["https://" + environ["APPLICATION_WEB_HOST"]]
