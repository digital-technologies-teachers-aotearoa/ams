"""Management command to toggle the unique constraint on Wagtail Site hostname/port.

This command allows you to remove or restore the unique constraint on
(hostname, port) in the wagtailcore_site table, which is necessary for
path-based multi-language routing where multiple Sites share the same hostname.

Usage:
    python manage.py modify_site_hostname_constraint --remove
    python manage.py modify_site_hostname_constraint --restore
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = (
        "Manage the unique constraint on Wagtail Site (hostname, port). "
        "Use --remove to allow multiple sites with same hostname:port, "
        "--restore to re-add the constraint, or --check to view current status."
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--remove",
            action="store_true",
            help="Remove the unique constraint to allow duplicate hostname:port",
        )
        group.add_argument(
            "--restore",
            action="store_true",
            help="Restore the unique constraint on (hostname, port)",
        )
        group.add_argument(
            "--check",
            action="store_true",
            help="Check the current state of the constraint without making changes",
        )

    def handle(self, *args, **options):
        if options["check"]:
            self._check_status()
        elif options["remove"]:
            self._remove_constraint()
        elif options["restore"]:
            self._restore_constraint()

    def _get_constraint_name(self):
        """Dynamically detect the name of the hostname/port unique constraint.

        Returns the constraint name if found, None otherwise.
        The constraint name can vary between databases (e.g., different hash suffixes).
        """
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

    def _check_duplicate_sites(self):
        """Check for existing duplicate hostname:port combinations.

        Returns a list of tuples: [(hostname, port, count), ...]
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT hostname, port, COUNT(*) as count
                FROM wagtailcore_site
                GROUP BY hostname, port
                HAVING COUNT(*) > 1;
                """,
            )
            return cursor.fetchall()

    def _display_duplicates(self, duplicates):
        """Display duplicate hostname:port combinations."""
        if duplicates:
            self.stdout.write(
                "\n" + self.style.NOTICE("Duplicate sites found:"),
            )
            for hostname, port, count in duplicates:
                self.stdout.write(f"  • {hostname}:{port} ({count} sites)")
        else:
            self.stdout.write("\nNo duplicate hostname:port combinations found.")

    def _print_header(self, title):
        """Print a formatted header."""
        separator = "=" * 70
        self.stdout.write(f"\n{separator}")
        self.stdout.write(self.style.NOTICE(title))
        self.stdout.write(f"{separator}\n")

    def _check_status(self):
        """Check and display the current state of the constraint."""
        constraint_name = self._get_constraint_name()

        self._print_header("WAGTAIL SITE CONSTRAINT STATUS")

        if constraint_name:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Unique constraint EXISTS: {constraint_name}",
                ),
            )
            self.stdout.write(
                "  Sites must have unique (hostname, port) combinations.",
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Unique constraint REMOVED",
                ),
            )
            self.stdout.write(
                "  Multiple sites can share the same hostname and port.",
            )

        # Check for duplicates
        duplicates = self._check_duplicate_sites()
        self._display_duplicates(duplicates)

        # Count total sites
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM wagtailcore_site;")
            total_sites = cursor.fetchone()[0]

        self.stdout.write(f"\nTotal sites: {total_sites}")
        self.stdout.write("=" * 70 + "\n")

    def _remove_constraint(self):
        """Remove the unique constraint on (hostname, port)."""
        constraint_name = self._get_constraint_name()

        if not constraint_name:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ No unique constraint found on (hostname, port).",
                ),
            )
            self.stdout.write("The constraint may have already been removed.")
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Removing constraint: {constraint_name}",
            ),
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"ALTER TABLE wagtailcore_site DROP CONSTRAINT {constraint_name};",
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully removed constraint: {constraint_name}",
                ),
            )
            self.stdout.write(
                "\nYou can now create multiple Sites with the same hostname and port.",
            )
            self.stdout.write(
                "Sites will be differentiated by SiteSettings.language field.",
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to remove constraint: {e}"))
            raise

    def _restore_constraint(self):
        """Restore the unique constraint on (hostname, port)."""
        constraint_name = self._get_constraint_name()

        if constraint_name:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ Unique constraint already exists on (hostname, port).",
                ),
            )
            self.stdout.write(f"   Constraint name: {constraint_name}")
            return

        # Check for duplicates before restoring
        duplicates = self._check_duplicate_sites()
        if duplicates:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Cannot restore constraint - duplicate sites exist:",
                ),
            )
            self._display_duplicates(duplicates)
            self.stdout.write(
                "\nYou must remove duplicate sites before restoring the constraint.",
            )
            self.stdout.write(
                "Use 'python manage.py shell' to delete unwanted sites.",
            )
            return

        self.stdout.write("Restoring unique constraint on (hostname, port)...")

        try:
            with connection.cursor() as cursor:
                # Use a predictable constraint name
                cursor.execute(
                    """
                    ALTER TABLE wagtailcore_site
                    ADD CONSTRAINT wagtailcore_site_hostname_port_uniq
                    UNIQUE (hostname, port);
                    """,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Successfully restored constraint: "
                    "wagtailcore_site_hostname_port_uniq",
                ),
            )
            self.stdout.write(
                "\nThe unique constraint on (hostname, port) is now active.",
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to restore constraint: {e}"))
            raise
