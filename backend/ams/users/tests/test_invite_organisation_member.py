from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from registration.models import RegistrationProfile

from ..models import Organisation, OrganisationMember, OrganisationType


class InviteOrganisationMemberFormTests(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(
            type=OrganisationType.objects.create(name="Primary School"),
            name="Any Organisation",
            telephone="555-12345",
            contact_name="John Smith",
            email="john@example.com",
            street_address="123 Main Street",
            suburb="Some Suburb",
            city="Capital City",
            postal_address="PO BOX 1234",
            postal_suburb="Some Suburb",
            postal_city="Capital City",
            postal_code="8080",
        )

        self.user = User.objects.create_user(username="testadminuser", is_staff=True)
        self.client.force_login(self.user)

        self.url = f"/users/organisations/invite/{self.organisation.pk}/"

    def test_should_not_allow_access_to_non_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(403, response.status_code)

    def test_should_allow_access_to_organisation_admin_user(self) -> None:
        # Given
        self.user.is_staff = False
        self.user.save()

        OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            invite_email=self.user.email,
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=timezone.localtime(),
            is_admin=True,
        )

        self.client.force_login(self.user)

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

    def test_get_endpoint(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "invite_organisation_member.html")

    def test_invite_existing_user_email_to_organisation(self) -> None:
        existing_user = User.objects.create_user(
            username="existinguser", first_name="John", email="user@example.com", is_staff=False, is_active=True
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, {"email": existing_user.email})

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/organisations/view/{self.organisation.pk}/?invite_sent=true", response.url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"You are invited to join {self.organisation.name}")

        organisation_member = OrganisationMember.objects.get(
            organisation=self.organisation, user=existing_user, invite_email=existing_user.email, accepted_datetime=None
        )

        self.assertEqual(len(organisation_member.invite_token), 64)
        self.assertEqual(
            mail.outbox[0].body,
            f"""Hello {existing_user.first_name},

You have been invited to join the organisation {self.organisation.name} in testserver.

Click the link below to accept the invitation.

https://testserver/users/accept-invite/{organisation_member.invite_token}/
""",
        )

    def test_invite_non_user_email_to_organisation(self) -> None:
        email = "non-user@example.com"

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, {"email": email})

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/organisations/view/{self.organisation.pk}/?invite_sent=true", response.url)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f"You are invited to join {self.organisation.name}")

        organisation_member = OrganisationMember.objects.get(
            organisation=self.organisation, user=None, invite_email=email, accepted_datetime=None
        )

        self.assertEqual(len(organisation_member.invite_token), 64)
        self.assertEqual(
            mail.outbox[0].body,
            f"""You have been invited to join the organisation {self.organisation.name} in testserver.

Click the link below to accept the invitation.

https://testserver/users/register-member/{organisation_member.invite_token}/

You will be asked to provide a password when accepting the invitation. """
            """After that you will be given access to the project and will be able to login.
""",
        )

    def test_should_validate_email_does_not_belong_to_member_of_organisation(self) -> None:
        # Given
        existing_user = User.objects.create_user(
            username="existinguser", first_name="John", email="user@example.com", is_staff=False, is_active=True
        )

        OrganisationMember.objects.create(
            user=existing_user,
            organisation=self.organisation,
            invite_email=existing_user.email,
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=timezone.localtime(),
        )

        # When
        response = self.client.post(self.url, {"email": existing_user.email})

        # Then
        expected_errors = {
            "email": ["A user with this email is already a member of this organisation."],
        }

        self.assertDictEqual(expected_errors, response.context["form"].errors)

    def test_user_accepts_invite(self) -> None:
        # Given
        existing_user = User.objects.create_user(
            username="existinguser", first_name="John", email="user@example.com", is_staff=False, is_active=True
        )

        response = self.client.post(self.url, {"email": existing_user.email})

        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/organisations/view/{self.organisation.pk}/?invite_sent=true", response.url)

        organisation_member = OrganisationMember.objects.get(
            organisation=self.organisation, user=existing_user, invite_email=existing_user.email, accepted_datetime=None
        )

        # When
        self.client.force_login(existing_user)
        response = self.client.get(f"/users/accept-invite/{organisation_member.invite_token}/")

        # Then
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "organisation_invite_accepted.html")

        organisation_member.refresh_from_db()
        self.assertIsNotNone(organisation_member.accepted_datetime)

    def test_wrong_user_tries_to_accept_invite(self) -> None:
        # Given
        existing_user = User.objects.create_user(
            username="existinguser", first_name="John", email="user@example.com", is_staff=False, is_active=True
        )

        response = self.client.post(self.url, {"email": existing_user.email})

        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/organisations/view/{self.organisation.pk}/?invite_sent=true", response.url)

        organisation_member = OrganisationMember.objects.get(
            organisation=self.organisation, user=existing_user, invite_email=existing_user.email, accepted_datetime=None
        )

        # When
        self.client.force_login(self.user)
        response = self.client.get(f"/users/accept-invite/{organisation_member.invite_token}/")

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/users/login/?next=/users/accept-invite/{organisation_member.invite_token}/", response.url)


class OrganisationUserRegistrationFormTests(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(
            type=OrganisationType.objects.create(name="Primary School"),
            name="Any Organisation",
            telephone="555-12345",
            contact_name="John Smith",
            email="john@example.com",
            street_address="123 Main Street",
            suburb="Some Suburb",
            city="Capital City",
            postal_address="PO BOX 1234",
            postal_suburb="Some Suburb",
            postal_city="Capital City",
            postal_code="8080",
        )

        self.user = User.objects.create_user(username="testadminuser", is_staff=True)
        self.client.force_login(self.user)

        self.organisation_member = OrganisationMember.objects.create(
            user=None,
            organisation=self.organisation,
            invite_email="new-user@example.com",
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=None,
        )

        self.form_values = {
            "first_name": "Jane",
            "last_name": "Smith",
            "password": "valid password",
            "confirm_password": "valid password",
        }

        self.url = f"/users/register-member/{self.organisation_member.invite_token}/"

    def test_new_user_registers_as_organisation_member(self) -> None:
        # Given
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url, self.form_values)

        # Then
        self.assertEqual(201, response.status_code)
        self.assertTemplateUsed(response, "individual_registration_pending.html")

        self.organisation_member.refresh_from_db()

        with self.subTest("invite accepted"):
            self.assertIsNotNone(self.organisation_member.accepted_datetime)

        with self.subTest("new user inactive created"):
            new_user = self.organisation_member.user

            self.assertEqual(new_user.email, self.organisation_member.invite_email)
            self.assertEqual(new_user.first_name, self.form_values["first_name"])
            self.assertEqual(new_user.last_name, self.form_values["last_name"])
            self.assertEqual(new_user.is_active, False)

        with self.subTest("created user billing account"):
            self.assertIsNotNone(self.organisation_member.user.account, None)

        with self.subTest("verification email sent"):
            activation_key = RegistrationProfile.objects.get(user=new_user).activation_key

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Account activation on testserver")

            self.assertEqual(
                mail.outbox[0].body,
                f"""Hello {new_user.first_name},

You're almost ready to start enjoying testserver.

Simply click the link below to verify your email address.

https://testserver/users/activate/{activation_key}/
""",
            )

    def test_should_check_password_is_valid(self) -> None:
        # Given
        self.form_values["password"] = "invalid"

        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        expected_errors = {
            "password": ["This password is too short. It must contain at least 8 characters."],
        }

        self.assertDictEqual(expected_errors, response.context["form"].errors)

    def test_should_check_confirm_password_matches(self) -> None:
        # Given
        self.form_values["confirm_password"] = "different password"

        # When
        response = self.client.post(self.url, self.form_values)

        # Then
        expected_errors = {
            "confirm_password": ["The two password fields didn't match."],
        }

        self.assertDictEqual(expected_errors, response.context["form"].errors)
