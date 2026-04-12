import re
from pathlib import Path
from urllib.parse import urlparse

import filetype
from django.utils.translation import gettext_lazy as _

TYPE_OTHER = 0
TYPE_DOCUMENT = 10
TYPE_PDF = 11
TYPE_IMAGE = 20
TYPE_SLIDESHOW = 30
TYPE_VIDEO = 40
TYPE_WEBSITE = 50
TYPE_AUDIO = 60
TYPE_ARCHIVE = 70
TYPE_RESOURCE = 80
TYPE_SPREADSHEET = 90

COMPONENT_TYPE_DATA = {
    TYPE_OTHER: {
        "icon": "file-earmark",
        "text": _("Other"),
    },
    TYPE_DOCUMENT: {
        "icon": "file-earmark-text",
        "text": _("Document"),
        "extensions": {
            "doc",
            "docx",
            "odt",
            "rtf",
            "tex",
            "txt",
            "wpd",
            "wks",
            "wps",
            "md",
            "markdown",
            "rst",
            "epub",
        },
    },
    TYPE_PDF: {
        "icon": "file-earmark-pdf",
        "text": _("PDF"),
        "extensions": {"pdf"},
    },
    TYPE_SPREADSHEET: {
        "icon": "file-earmark-spreadsheet",
        "text": _("Spreadsheet"),
        "extensions": {"xlr", "xls", "xlsx", "ods"},
    },
    TYPE_IMAGE: {
        "icon": "file-earmark-image",
        "text": _("Image"),
    },
    TYPE_SLIDESHOW: {
        "icon": "file-earmark-slides",
        "text": _("Slideshow"),
    },
    TYPE_VIDEO: {
        "icon": "file-earmark-play",
        "text": _("Video"),
        "url_regexes": {
            r"^(http(s)?://)?((w){3}.)?youtu(be|.be)?(.com)?/.+",
            r"^(http(s)?://)?((w){3}.|player.)?vimeo(.com)?/.+",
        },
    },
    TYPE_WEBSITE: {
        "icon": "globe2",
        "text": _("Website"),
    },
    TYPE_AUDIO: {
        "icon": "file-earmark-music",
        "text": _("Audio"),
    },
    TYPE_ARCHIVE: {
        "icon": "file-earmark-zip",
        "text": _("Archive"),
    },
    TYPE_RESOURCE: {
        "icon": "folder-symlink",
        "text": _("Resource"),
    },
}

COMPONENT_TYPE_CHOICES = tuple(
    (value, data["text"]) for value, data in COMPONENT_TYPE_DATA.items()
)

GOOGLE_DRIVE_HOSTS = {"drive.google.com", "docs.google.com"}
GOOGLE_DRIVE_PATH_MAP = {
    "document": TYPE_DOCUMENT,
    "spreadsheets": TYPE_SPREADSHEET,
    "presentation": TYPE_SLIDESHOW,
    "drawings": TYPE_IMAGE,
    "file": TYPE_OTHER,
}


def detect_url_type(url: str) -> int:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host in GOOGLE_DRIVE_HOSTS:
        segments = [segment for segment in parsed.path.split("/") if segment]
        if segments and segments[0] in GOOGLE_DRIVE_PATH_MAP:
            return GOOGLE_DRIVE_PATH_MAP[segments[0]]
        return TYPE_WEBSITE
    for type_code, type_data in COMPONENT_TYPE_DATA.items():
        for regex in type_data.get("url_regexes", set()):
            if re.match(regex, url):
                return type_code
    return TYPE_WEBSITE


def detect_file_type(file_field) -> int:
    extension = Path(file_field.name).suffix[1:].lower()
    for type_code, type_data in COMPONENT_TYPE_DATA.items():
        if extension in type_data.get("extensions", set()):
            return type_code

    file_obj = file_field.open()
    try:
        if filetype.helpers.is_image(file_obj):
            return TYPE_IMAGE
        if filetype.helpers.is_video(file_obj):
            return TYPE_VIDEO
        if filetype.helpers.is_audio(file_obj):
            return TYPE_AUDIO
        if filetype.helpers.is_archive(file_obj):
            return TYPE_ARCHIVE
    finally:
        file_obj.seek(0)
    return TYPE_OTHER
