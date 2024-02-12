import re

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.test import RequestFactory, TestCase
from registration.models import RegistrationProfile


class UserPasswordResetTests(TestCase):
    def setUp(self) -> None:
        request = RequestFactory().get("/")

        self.user = RegistrationProfile.objects.create_inactive_user(
            get_current_site(request),
            send_email=False,
            username="user@example.com",
            email="user@example.com",
            first_name="John",
            last_name="Smith",
            password="valid password",
        )
        self.user.is_active = True
        self.user.save()

    def test_password_reset_sends_expected_email(self) -> None:
        site = Site.objects.get()

        # When
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/users/password/reset/", {"email": self.user.email})

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(response.url, "/users/password/reset/done/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"Password reset on {site.name}")

        body = mail.outbox[0].body
        body = re.sub(r"/confirm/[A-za-z0-9-/]+", "/confirm/TOKEN", body, count=2)

        self.maxDiff = None
        self.assertEqual(
            body,
            f"""Hello {self.user.first_name},

You are receiving this email because you (or someone pretending to be you)
requested that your password be reset on {site.name}. If you do not
wish to reset your password, please ignore this message.

To reset your password, please click the following link:

https://{site.domain}/users/password/reset/confirm/TOKEN
""",
        )
