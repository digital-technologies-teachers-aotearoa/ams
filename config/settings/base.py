# ruff: noqa: E501
"""Base settings to build other settings files upon."""

from pathlib import Path

import django.conf.locale
import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# ams/
APPS_DIR = BASE_DIR / "ams"
env = environ.Env()

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Pacific/Auckland"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en"
# https://docs.djangoproject.com/en/dev/ref/settings/#languages
LANGUAGES = [
    ("en", _("English")),
    ("mi", _("Te Reo Māori")),
]
EXTRA_LANG_INFO = {
    "mi": {
        "bidi": False,
        "code": "mi",
        "name": "Te Reo Māori",
        "name_local": "Te Reo Māori",
    },
}
django.conf.locale.LANG_INFO.update(EXTRA_LANG_INFO)

# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
APPEND_SLASH = True
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "allauth.socialaccount",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
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
    "wagtailmenus",
    "modelcluster",
    "taggit",
    "storages",
]

LOCAL_APPS = [
    "ams.users",
    "ams.cms",
    "ams.memberships",
    "ams.billing",
    "ams.utils",
    "ams.forum",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "ams.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "users:redirect"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "ams.utils.middleware.site_by_path.PathBasedSiteMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "config.storage_backends.PublicMediaStorage",
        "OPTIONS": {
            "bucket_name": env("DJANGO_MEDIA_PUBLIC_BUCKET_NAME"),
            "endpoint_url": env("DJANGO_MEDIA_PUBLIC_ENDPOINT_URL"),
            "access_key": env("DJANGO_MEDIA_PUBLIC_ACCESS_KEY"),
            "secret_key": env("DJANGO_MEDIA_PUBLIC_SECRET_KEY"),
            "region_name": env("DJANGO_MEDIA_PUBLIC_REGION_NAME", default=None),
            "custom_domain": env("DJANGO_MEDIA_PUBLIC_CUSTOM_DOMAIN", default=None),
        },
    },
    "private": {
        "BACKEND": "config.storage_backends.PrivateMediaStorage",
        "OPTIONS": {
            "bucket_name": env("DJANGO_MEDIA_PRIVATE_BUCKET_NAME"),
            "endpoint_url": env("DJANGO_MEDIA_PRIVATE_ENDPOINT_URL"),
            "access_key": env("DJANGO_MEDIA_PRIVATE_ACCESS_KEY"),
            "secret_key": env("DJANGO_MEDIA_PRIVATE_SECRET_KEY"),
            "region_name": env("DJANGO_MEDIA_PRIVATE_REGION_NAME", default=None),
            "custom_domain": env("DJANGO_MEDIA_PRIVATE_CUSTOM_DOMAIN", default=None),
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        "DIRS": [str(APPS_DIR / "templates")],
        # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
        "APP_DIRS": True,
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
                "ams.users.context_processors.allauth_settings",
                "wagtailmenus.context_processors.wagtailmenus",
            ],
            "libraries": {
                "icon": "config.templatetags.icon",
                "translate_url": "config.templatetags.translate_url",
            },
        },
    },
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""DTTA""", "admin@dtta.org.nz")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# https://cookiecutter-django.readthedocs.io/en/latest/settings.html#other-environment-settings
# Force the `admin` sign in process to go through the `django-allauth` workflow
DJANGO_ADMIN_FORCE_ALLAUTH = env.bool("DJANGO_ADMIN_FORCE_ALLAUTH", default=True)

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


# django-allauth
# ------------------------------------------------------------------------------


def display_user(user):
    return user.get_full_name()


# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
    "username*",
]
ACCOUNT_USER_DISPLAY = display_user
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "ams.users.adapters.AccountAdapter"
# https://docs.allauth.org/en/latest/account/forms.html
ACCOUNT_FORMS = {"signup": "ams.users.forms.UserSignupForm"}
# https://docs.allauth.org/en/latest/socialaccount/configuration.html
SOCIALACCOUNT_ADAPTER = "ams.users.adapters.SocialAccountAdapter"
# https://docs.allauth.org/en/latest/socialaccount/configuration.html
SOCIALACCOUNT_FORMS = {"signup": "ams.users.forms.UserSocialSignupForm"}


# Wagtail
# ------------------------------------------------------------------------------
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000
WAGTAIL_ENABLE_UPDATE_CHECK = "lts"
WAGTAIL_SITE_NAME = "AMS Demo"
WAGTAIL_APPEND_SLASH = True
WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES
WAGTAILADMIN_BASE_URL = env("SITE_DOMAIN", default="ams.com") + "/cms/"
WAGTAILIMAGES_EXTENSIONS = ["avif", "gif", "jpg", "jpeg", "png", "webp", "svg"]
WAGTAILDOCS_DOCUMENT_MODEL = "cms.AMSDocument"
WAGTAILDOCS_SERVE_METHOD = "serve_view"
WAGTAILDOCS_EXTENSIONS = [
    *WAGTAILIMAGES_EXTENSIONS,
    "csv",
    "docx",
    "key",
    "odt",
    "pdf",
    "pptx",
    "rtf",
    "txt",
    "xlsx",
    "zip",
]
WAGTAILEMBEDS_RESPONSIVE_HTML = True
WAGTAILMENUS_FLAT_MENUS_HANDLE_CHOICES = (
    ("footer-1", "Footer - Column 1"),
    ("footer-2", "Footer - Column 2"),
    ("footer-3", "Footer - Column 3"),
)
WAGTAIL_AMS_ADMIN_HELPERS = env.bool("DJANGO_WAGTAIL_AMS_ADMIN_HELPERS", default=True)


# Discourse SSO
# ------------------------------------------------------------------------------
DISCOURSE_REDIRECT_DOMAIN = env("DISCOURSE_REDIRECT_DOMAIN", default=None)
DISCOURSE_CONNECT_SECRET = env("DISCOURSE_CONNECT_SECRET", default=None)


# Django Tables2
# ------------------------------------------------------------------------------
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap5-responsive.html"


# Sample data generation
# ------------------------------------------------------------------------------
# Admin
SAMPLE_DATA_ADMIN_EMAIL = env("SAMPLE_DATA_ADMIN_EMAIL", default="admin@ams.com")
SAMPLE_DATA_ADMIN_PASSWORD = env("SAMPLE_DATA_ADMIN_PASSWORD", default="password")
# User
SAMPLE_DATA_USER_EMAIL = env("SAMPLE_DATA_USER_EMAIL", default="user@ams.com")
SAMPLE_DATA_USER_PASSWORD = env("SAMPLE_DATA_USER_PASSWORD", default="password")


# Documentation
# ------------------------------------------------------------------------------
DOCUMENTATION_URL = env(
    "DOCUMENTATION_URL",
    default="https://digital-technologies-teachers-aotearoa.github.io/ams/",
)

# Other settings
# ------------------------------------------------------------------------------
DEPLOYED = env.bool("DEPLOYED", default=False)
SITE_DOMAIN = env("SITE_DOMAIN", default="ams.com")
SITE_PORT = env.int("SITE_PORT", default=80)
