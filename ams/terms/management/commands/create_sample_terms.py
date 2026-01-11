"""Management command to create sample Terms and TermVersions for development."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from ams.terms.models import Term
from ams.terms.models import TermVersion


class Command(BaseCommand):
    """Create sample Terms and TermVersions for development and testing."""

    help = "Create sample Terms and TermVersions for development"

    def handle(self, *args, **options):
        """Create sample terms."""
        self.stdout.write("Creating sample terms and versions...\n")

        # Create Privacy Policy
        privacy, created = Term.objects.get_or_create(
            key="privacy-policy",
            defaults={
                "name": "Privacy Policy",
                "description": "Privacy policy for the application",
            },
        )

        if created:
            self.stdout.write(f"✓ Created Term: {privacy.name}")
        else:
            self.stdout.write(f"⊘ Term already exists: {privacy.name}")

        # Create Privacy Policy version
        privacy_version, created = TermVersion.objects.get_or_create(
            term=privacy,
            version="1.0",
            defaults={
                "content": """
                    <h2>Privacy Policy</h2>
                    <p>This is a sample privacy policy.</p>
                    <p>We collect and process your personal data in accordance with
                    applicable laws.</p>
                    <h3>Data Collection</h3>
                    <p>We collect the following information:</p>
                    <ul>
                        <li>Name and email address</li>
                        <li>Usage data and analytics</li>
                        <li>IP address and browser information</li>
                    </ul>
                    <h3>Data Usage</h3>
                    <p>Your data is used to provide and improve our services.</p>
                    <p>We do not sell your personal information to third parties.</p>
                """,
                "change_log": "Initial version",
                "is_active": True,
                "date_active": timezone.now(),
            },
        )

        if created:
            self.stdout.write(f"✓ Created TermVersion: {privacy_version}")
        else:
            self.stdout.write(f"⊘ TermVersion already exists: {privacy_version}")

        # Create Terms of Service
        tos, created = Term.objects.get_or_create(
            key="terms-of-service",
            defaults={
                "name": "Terms of Service",
                "description": "Terms of service for using the application",
            },
        )

        if created:
            self.stdout.write(f"✓ Created Term: {tos.name}")
        else:
            self.stdout.write(f"⊘ Term already exists: {tos.name}")

        # Create Terms of Service version
        tos_version, created = TermVersion.objects.get_or_create(
            term=tos,
            version="1.0",
            defaults={
                "content": """
                    <h2>Terms of Service</h2>
                    <p>This is a sample terms of service agreement.</p>
                    <h3>Acceptance of Terms</h3>
                    <p>By accessing and using this service, you accept and agree to be
                    bound by these terms.</p>
                    <h3>User Responsibilities</h3>
                    <ul>
                        <li>You must provide accurate information</li>
                        <li>You are responsible for maintaining account security</li>
                        <li>You agree to use the service in compliance with all
                        applicable laws</li>
                    </ul>
                    <h3>Prohibited Activities</h3>
                    <p>You may not use this service to:</p>
                    <ul>
                        <li>Violate any laws or regulations</li>
                        <li>Infringe on intellectual property rights</li>
                        <li>Transmit malicious code or spam</li>
                    </ul>
                    <h3>Termination</h3>
                    <p>We reserve the right to terminate accounts that violate these
                    terms.</p>
                """,
                "change_log": "Initial version",
                "is_active": True,
                "date_active": timezone.now(),
            },
        )

        if created:
            self.stdout.write(f"✓ Created TermVersion: {tos_version}")
        else:
            self.stdout.write(f"⊘ TermVersion already exists: {tos_version}")

        self.stdout.write("\n✅ Sample terms creation completed!\n")
