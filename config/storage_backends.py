from storages.backends.s3 import S3Storage


class PublicMediaStorage(S3Storage):
    default_acl = "public-read"
    querystring_auth = False
    file_overwrite = False


class PrivateMediaStorage(S3Storage):
    default_acl = "private"
    querystring_auth = True
    file_overwrite = True
