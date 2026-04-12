from pathlib import Path


def resource_upload_path(instance, filename):
    return Path("resources") / str(instance.resource.pk) / filename
