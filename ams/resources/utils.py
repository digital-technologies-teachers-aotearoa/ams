from datetime import UTC
from datetime import datetime
from pathlib import Path


def resource_upload_path(instance, filename):
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    subdir = f"{instance.uuid}_{timestamp}"
    return Path("resources") / str(instance.resource.pk) / subdir / filename
