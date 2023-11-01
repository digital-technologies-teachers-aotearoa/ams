from os import environ

from ..settings import Common


class DTTACommon(Common):
    INSTALLED_APPS = Common.INSTALLED_APPS + ["ams.dtta"]

    TIME_ZONE = "Pacific/Auckland"

    SHORT_DATE_FORMAT = "d/m/Y"

    DATE_INPUT_FORMATS = ["%Y-%m-%d", "%d/%m/%Y"]

    WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
        ("en", "English"),
        ("mi", "Maori"),
    ]

    EXTRA_LANG_INFO = {
        "mi": {
            "bidi": False,
            "code": "mi",
            "name": "Maori",
            "name_local": "Māori",
        },
    }


class Development(DTTACommon):
    DEBUG = True
    CSRF_TRUSTED_ORIGINS = ["http://" + environ["APPLICATION_WEB_HOST"] + ":1800"]


class Test(Development):
    MEDIA_ROOT = None
    DISCOURSE_API_KEY = None


class Testing(DTTACommon):
    DEBUG = False
    CSRF_TRUSTED_ORIGINS = ["https://" + environ["APPLICATION_WEB_HOST"]]
