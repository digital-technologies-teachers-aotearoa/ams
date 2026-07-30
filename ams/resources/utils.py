from datetime import UTC
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def resource_upload_path(instance, filename):
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    subdir = f"{instance.uuid}_{timestamp}"
    return Path("resources") / str(instance.resource.pk) / subdir / filename


def resource_thumbnail_path(instance, filename):
    extension = filename.split(".")[-1] if "." in filename else "jpg"
    return f"resources/thumbnails/{uuid4().hex}.{extension}"
