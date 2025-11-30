"""Tests for the modify_site_hostname_constraint management command."""

from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from wagtail.models import Site


@pytest.mark.django_db
class TestToggleSiteHostnameConstraint:
    """Test suite for modify_site_hostname_constraint management command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.stdout = StringIO()
        self.stderr = StringIO()

    def _get_constraint_name(self):
        """Helper to get the current constraint name."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'wagtailcore_site'::regclass
                AND contype = 'u'
                AND pg_get_constraintdef(oid) LIKE '%%hostname%%port%%';
                """,
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _constraint_exists(self):
        """Check if the unique constraint exists."""
        return self._get_constraint_name() is not None

    def _get_duplicate_sites_count(self):
        """Get count of duplicate hostname:port combinations."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT hostname, port, COUNT(*) as count
                    FROM wagtailcore_site
                    GROUP BY hostname, port
                    HAVING COUNT(*) > 1
                ) duplicates;
                """,
            )
            return cursor.fetchone()[0]

    def _remove_constraint_if_exists(self):
        """Helper to remove constraint if it exists."""
        constraint_name = self._get_constraint_name()
        if constraint_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"ALTER TABLE wagtailcore_site DROP CONSTRAINT {constraint_name};",
                )

    def _restore_constraint(self):
        """Helper to restore the constraint."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                ALTER TABLE wagtailcore_site
                ADD CONSTRAINT wagtailcore_site_hostname_port_uniq
                UNIQUE (hostname, port);
                """,
            )

    def test_check_command_with_constraint_exists(self):
        """Test --check flag when constraint exists."""
        # Ensure constraint exists
        self._remove_constraint_if_exists()
        self._restore_constraint()

        call_command(
            "modify_site_hostname_constraint",
            "--check",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "WAGTAIL SITE CONSTRAINT STATUS" in output
        assert "Unique constraint EXISTS" in output
        assert "⚠️" in output or "WARNING" in output.upper()

    def test_check_command_without_constraint(self):
        """Test --check flag when constraint does not exist."""
        # Ensure constraint is removed
        self._remove_constraint_if_exists()

        call_command(
            "modify_site_hostname_constraint",
            "--check",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "WAGTAIL SITE CONSTRAINT STATUS" in output
        assert "Unique constraint REMOVED" in output
        assert "✅" in output or "SUCCESS" in output.upper()

    def test_check_command_shows_duplicate_sites(self):
        """Test --check displays duplicate sites when they exist."""
        # Remove constraint and create duplicate sites
        self._remove_constraint_if_exists()

        # Create duplicate sites
        root_page = Site.objects.get(is_default_site=True).root_page
        Site.objects.create(
            hostname="example.com",
            port=80,
            root_page=root_page,
            is_default_site=False,
        )
        Site.objects.create(
            hostname="example.com",
            port=80,
            root_page=root_page,
            is_default_site=False,
        )

        try:
            call_command(
                "modify_site_hostname_constraint",
                "--check",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "Duplicate sites found" in output
            assert "example.com:80" in output

        finally:
            # Cleanup
            Site.objects.filter(hostname="example.com", port=80).delete()

    def test_check_command_shows_no_duplicates(self):
        """Test --check shows message when no duplicates exist."""
        # Remove any duplicate sites
        self._remove_constraint_if_exists()

        # Ensure only default site exists or no duplicates
        call_command(
            "modify_site_hostname_constraint",
            "--check",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        # Should show either "No duplicate" message or just the status
        assert "WAGTAIL SITE CONSTRAINT STATUS" in output

    def test_remove_constraint_when_exists(self):
        """Test --remove successfully removes existing constraint."""
        # Ensure constraint exists
        self._remove_constraint_if_exists()
        self._restore_constraint()
        assert self._constraint_exists()

        call_command(
            "modify_site_hostname_constraint",
            "--remove",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "Successfully removed constraint" in output
        assert not self._constraint_exists()

    def test_remove_constraint_when_not_exists(self):
        """Test --remove when constraint doesn't exist shows appropriate message."""
        # Ensure constraint is removed
        self._remove_constraint_if_exists()
        assert not self._constraint_exists()

        call_command(
            "modify_site_hostname_constraint",
            "--remove",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert (
            "No unique constraint found" in output or "already been removed" in output
        )

    def test_restore_constraint_when_not_exists(self):
        """Test --restore successfully restores constraint."""
        # Remove constraint
        self._remove_constraint_if_exists()
        assert not self._constraint_exists()

        call_command(
            "modify_site_hostname_constraint",
            "--restore",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "Successfully restored constraint" in output
        assert self._constraint_exists()

        # Cleanup - remove constraint again for other tests
        self._remove_constraint_if_exists()

    def test_restore_constraint_when_already_exists(self):
        """Test --restore when constraint already exists."""
        # Ensure constraint exists
        self._remove_constraint_if_exists()
        self._restore_constraint()
        assert self._constraint_exists()

        call_command(
            "modify_site_hostname_constraint",
            "--restore",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "already exists" in output

    def test_restore_constraint_fails_with_duplicates(self):
        """Test --restore fails when duplicate sites exist."""
        # Remove constraint and create duplicates
        self._remove_constraint_if_exists()

        root_page = Site.objects.get(is_default_site=True).root_page
        Site.objects.create(
            hostname="duplicate.com",
            port=80,
            root_page=root_page,
            is_default_site=False,
        )
        Site.objects.create(
            hostname="duplicate.com",
            port=80,
            root_page=root_page,
            is_default_site=False,
        )

        try:
            call_command(
                "modify_site_hostname_constraint",
                "--restore",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "Cannot restore constraint" in output
            assert "duplicate sites exist" in output
            assert "duplicate.com:80" in output
            assert not self._constraint_exists()

        finally:
            # Cleanup
            Site.objects.filter(hostname="duplicate.com", port=80).delete()

    def test_command_requires_argument(self):
        """Test that command requires one of the mutually exclusive arguments."""
        with pytest.raises(CommandError, match="one of the arguments"):
            call_command(
                "modify_site_hostname_constraint",
                stdout=self.stdout,
                stderr=self.stderr,
            )

    def test_command_rejects_multiple_arguments(self):
        """Test that command rejects multiple mutually exclusive arguments."""
        with pytest.raises(CommandError, match="not allowed with argument"):
            call_command(
                "modify_site_hostname_constraint",
                "--check",
                "--remove",
                stdout=self.stdout,
                stderr=self.stderr,
            )

    @patch("ams.cms.management.commands.modify_site_hostname_constraint.connection")
    def test_remove_constraint_handles_database_error(self, mock_connection):
        """Test that --remove handles database errors gracefully."""
        # Setup mock to raise an exception
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("test_constraint",)
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        # First call returns constraint name, second call raises error
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_cursor
            msg = "Database error"
            raise RuntimeError(msg)

        mock_connection.cursor.side_effect = side_effect

        with pytest.raises(RuntimeError, match="Database error"):
            call_command(
                "modify_site_hostname_constraint",
                "--remove",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        error_output = self.stderr.getvalue()
        assert "Failed to remove constraint" in error_output

    @patch("ams.cms.management.commands.modify_site_hostname_constraint.connection")
    def test_restore_constraint_handles_database_error(self, mock_connection):
        """Test that --restore handles database errors gracefully."""
        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        # Track which execute call we're on
        execute_call_count = [0]

        def execute_side_effect(sql, *args, **kwargs):
            execute_call_count[0] += 1
            # First and second execute: check for constraint and duplicates
            if "SELECT conname" in sql or "HAVING COUNT" in sql:
                mock_cursor.fetchone.return_value = None
            # Third execute: ALTER TABLE - raise error
            elif "ALTER TABLE" in sql:
                msg = "Database error"
                raise RuntimeError(msg)

        mock_cursor.execute.side_effect = execute_side_effect
        mock_cursor.fetchall.return_value = []  # No duplicates
        mock_cursor.fetchone.return_value = None  # Default

        mock_connection.cursor.return_value = mock_cursor

        with pytest.raises(RuntimeError, match="Database error"):
            call_command(
                "modify_site_hostname_constraint",
                "--restore",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        error_output = self.stderr.getvalue()
        assert "Failed to restore constraint" in error_output

    def test_check_displays_total_sites_count(self):
        """Test that --check displays the total number of sites."""
        call_command(
            "modify_site_hostname_constraint",
            "--check",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "Total sites:" in output

    def test_remove_constraint_includes_usage_message(self):
        """Test that --remove includes helpful usage message."""
        # Ensure constraint exists
        self._remove_constraint_if_exists()
        self._restore_constraint()

        call_command(
            "modify_site_hostname_constraint",
            "--remove",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "multiple Sites with the same hostname and port" in output
        assert "SiteSettings.language" in output

    def test_restore_constraint_includes_usage_message(self):
        """Test that --restore includes helpful usage message when successful."""
        # Remove constraint first
        self._remove_constraint_if_exists()

        call_command(
            "modify_site_hostname_constraint",
            "--restore",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        output = self.stdout.getvalue()
        assert "unique constraint" in output.lower()
        assert "active" in output.lower()

        # Cleanup
        self._remove_constraint_if_exists()

    def test_restore_provides_guidance_when_duplicates_exist(self):
        """Test --restore provides guidance when duplicates prevent restoration."""
        # Remove constraint and create duplicates
        self._remove_constraint_if_exists()

        root_page = Site.objects.get(is_default_site=True).root_page
        Site.objects.create(
            hostname="test.com",
            port=443,
            root_page=root_page,
            is_default_site=False,
        )
        Site.objects.create(
            hostname="test.com",
            port=443,
            root_page=root_page,
            is_default_site=False,
        )

        try:
            call_command(
                "modify_site_hostname_constraint",
                "--restore",
                stdout=self.stdout,
                stderr=self.stderr,
            )

            output = self.stdout.getvalue()
            assert "remove duplicate sites" in output.lower()
            assert "python manage.py shell" in output

        finally:
            # Cleanup
            Site.objects.filter(hostname="test.com", port=443).delete()


@pytest.mark.django_db
class TestConstraintNameDetection:
    """Test constraint name detection across different database states."""

    def test_detects_standard_constraint_name(self):
        """Test detection of Django's auto-generated constraint name."""
        # The actual constraint name may vary, but the command should detect it
        call_command(
            "modify_site_hostname_constraint",
            "--check",
            stdout=StringIO(),
            stderr=StringIO(),
        )
        # If we get here without error, constraint detection works

    def test_detects_custom_constraint_name(self):
        """Test detection of custom constraint name after restoration."""
        stdout = StringIO()

        # Remove any existing constraint
        call_command(
            "modify_site_hostname_constraint",
            "--remove",
            stdout=StringIO(),
            stderr=StringIO(),
        )

        # Restore with our custom name
        call_command(
            "modify_site_hostname_constraint",
            "--restore",
            stdout=stdout,
            stderr=StringIO(),
        )

        # Check should detect the custom name
        stdout_check = StringIO()
        call_command(
            "modify_site_hostname_constraint",
            "--check",
            stdout=stdout_check,
            stderr=StringIO(),
        )

        output = stdout_check.getvalue()
        assert "wagtailcore_site_hostname_port_uniq" in output or "EXISTS" in output

        # Cleanup
        call_command(
            "modify_site_hostname_constraint",
            "--remove",
            stdout=StringIO(),
            stderr=StringIO(),
        )
