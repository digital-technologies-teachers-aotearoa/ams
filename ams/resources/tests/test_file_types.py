from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile

from ams.resources.file_types import TYPE_ARCHIVE
from ams.resources.file_types import TYPE_AUDIO
from ams.resources.file_types import TYPE_DOCUMENT
from ams.resources.file_types import TYPE_IMAGE
from ams.resources.file_types import TYPE_OTHER
from ams.resources.file_types import TYPE_PDF
from ams.resources.file_types import TYPE_SLIDESHOW
from ams.resources.file_types import TYPE_SPREADSHEET
from ams.resources.file_types import TYPE_VIDEO
from ams.resources.file_types import TYPE_WEBSITE
from ams.resources.file_types import detect_file_type
from ams.resources.file_types import detect_url_type


def _make_file(name, content=b"data"):
    return SimpleUploadedFile(name, content)


class TestDetectUrlType:
    def test_youtube_www_url(self):
        assert detect_url_type("https://www.youtube.com/watch?v=abc123") == TYPE_VIDEO

    def test_youtube_short_url(self):
        assert detect_url_type("https://youtu.be/abc123") == TYPE_VIDEO

    def test_youtube_without_www(self):
        assert detect_url_type("https://youtube.com/watch?v=abc123") == TYPE_VIDEO

    def test_vimeo_url(self):
        assert detect_url_type("https://vimeo.com/12345") == TYPE_VIDEO

    def test_vimeo_player_url(self):
        assert detect_url_type("https://player.vimeo.com/video/12345") == TYPE_VIDEO

    def test_google_docs_document(self):
        assert (
            detect_url_type("https://docs.google.com/document/d/abc123/edit")
            == TYPE_DOCUMENT
        )

    def test_google_docs_spreadsheet(self):
        assert (
            detect_url_type("https://docs.google.com/spreadsheets/d/abc123/edit")
            == TYPE_SPREADSHEET
        )

    def test_google_docs_presentation(self):
        assert (
            detect_url_type("https://docs.google.com/presentation/d/abc123/edit")
            == TYPE_SLIDESHOW
        )

    def test_google_docs_drawing(self):
        assert (
            detect_url_type("https://docs.google.com/drawings/d/abc123/edit")
            == TYPE_IMAGE
        )

    def test_google_docs_file(self):
        assert detect_url_type("https://docs.google.com/file/d/abc123") == TYPE_OTHER

    def test_google_drive_file(self):
        assert detect_url_type("https://drive.google.com/file/d/abc123") == TYPE_OTHER

    def test_google_drive_unknown_path_returns_website(self):
        assert detect_url_type("https://docs.google.com/forms/d/abc123") == TYPE_WEBSITE

    def test_generic_https_url(self):
        assert detect_url_type("https://example.com/path/to/page") == TYPE_WEBSITE

    def test_generic_http_url(self):
        assert detect_url_type("http://example.org") == TYPE_WEBSITE


class TestDetectFileType:
    def test_pdf_extension(self):
        assert detect_file_type(_make_file("report.pdf")) == TYPE_PDF

    def test_doc_extension(self):
        assert detect_file_type(_make_file("report.doc")) == TYPE_DOCUMENT

    def test_docx_extension(self):
        assert detect_file_type(_make_file("report.docx")) == TYPE_DOCUMENT

    def test_odt_extension(self):
        assert detect_file_type(_make_file("report.odt")) == TYPE_DOCUMENT

    def test_rtf_extension(self):
        assert detect_file_type(_make_file("report.rtf")) == TYPE_DOCUMENT

    def test_txt_extension(self):
        assert detect_file_type(_make_file("notes.txt")) == TYPE_DOCUMENT

    def test_md_extension(self):
        assert detect_file_type(_make_file("readme.md")) == TYPE_DOCUMENT

    def test_rst_extension(self):
        assert detect_file_type(_make_file("readme.rst")) == TYPE_DOCUMENT

    def test_epub_extension(self):
        assert detect_file_type(_make_file("book.epub")) == TYPE_DOCUMENT

    def test_tex_extension(self):
        assert detect_file_type(_make_file("paper.tex")) == TYPE_DOCUMENT

    def test_wpd_extension(self):
        assert detect_file_type(_make_file("document.wpd")) == TYPE_DOCUMENT

    def test_xls_extension(self):
        assert detect_file_type(_make_file("data.xls")) == TYPE_SPREADSHEET

    def test_xlsx_extension(self):
        assert detect_file_type(_make_file("data.xlsx")) == TYPE_SPREADSHEET

    def test_ods_extension(self):
        assert detect_file_type(_make_file("data.ods")) == TYPE_SPREADSHEET

    def test_xlr_extension(self):
        assert detect_file_type(_make_file("data.xlr")) == TYPE_SPREADSHEET

    def test_binary_image_detection(self):
        with patch("filetype.helpers.is_image", return_value=True):
            assert detect_file_type(_make_file("photo.bin")) == TYPE_IMAGE

    def test_binary_video_detection(self):
        with (
            patch("filetype.helpers.is_image", return_value=False),
            patch("filetype.helpers.is_video", return_value=True),
        ):
            assert detect_file_type(_make_file("clip.bin")) == TYPE_VIDEO

    def test_binary_audio_detection(self):
        with (
            patch("filetype.helpers.is_image", return_value=False),
            patch("filetype.helpers.is_video", return_value=False),
            patch("filetype.helpers.is_audio", return_value=True),
        ):
            assert detect_file_type(_make_file("track.bin")) == TYPE_AUDIO

    def test_binary_archive_detection(self):
        with (
            patch("filetype.helpers.is_image", return_value=False),
            patch("filetype.helpers.is_video", return_value=False),
            patch("filetype.helpers.is_audio", return_value=False),
            patch("filetype.helpers.is_archive", return_value=True),
        ):
            assert detect_file_type(_make_file("bundle.bin")) == TYPE_ARCHIVE

    def test_unknown_binary_returns_other(self):
        with (
            patch("filetype.helpers.is_image", return_value=False),
            patch("filetype.helpers.is_video", return_value=False),
            patch("filetype.helpers.is_audio", return_value=False),
            patch("filetype.helpers.is_archive", return_value=False),
        ):
            assert detect_file_type(_make_file("unknown.bin")) == TYPE_OTHER
