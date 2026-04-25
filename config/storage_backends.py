from django.conf import settings
from storages.backends.s3 import S3Storage


class PublicMediaStorage(S3Storage):
    default_acl = "public-read"
    querystring_auth = False
    file_overwrite = False

    def __init__(self, **kwargs):
        class_path = f"{self.__class__.__module__}.{self.__class__.__name__}"
        default_config = settings.STORAGES.get("default", {})
        if default_config.get("BACKEND") == class_path:
            options = default_config.get("OPTIONS", {})
            kwargs = {**options, **kwargs}
        super().__init__(**kwargs)


class PrivateMediaStorage(S3Storage):
    default_acl = "private"
    querystring_auth = True
    file_overwrite = False

    def __init__(self, **kwargs):
        class_path = f"{self.__class__.__module__}.{self.__class__.__name__}"
        private_config = settings.STORAGES.get("private", {})
        if private_config.get("BACKEND") == class_path:
            options = private_config.get("OPTIONS", {})
            kwargs = {**options, **kwargs}
        super().__init__(**kwargs)
