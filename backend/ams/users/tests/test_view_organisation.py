from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from ...test.utils import (
    any_invoice,
    any_organisation,
    any_organisation_account,
    parse_response_table_rows,
)
from ..models import (
    MembershipOption,
    MembershipOptionType,
    Organisation,
    OrganisationMember,
    OrganisationMembership,
    OrganisationType,
)


class ViewOrganisationFormTests(TestCase):
    def setUp(self) -> None:
        self.organisation = any_organisation()

        self.user = User.objects.create_user(
            username="testadminuser", email="user@example.com", first_name="John", last_name="Smith", is_staff=True
        )

        self.organisation_member = OrganisationMember.objects.create(
            user=self.user,
            organisation=self.organisation,
            invite_email=self.user.email,
            invite_token="token",
            created_datetime=timezone.localtime(),
            accepted_datetime=timezone.localtime(),
        )

        membership_option = MembershipOption.objects.create(
            name="Membership Option", type=MembershipOptionType.ORGANISATION, duration="P1M", cost="1.00"
        )

        start = timezone.localtime() - relativedelta(days=7)

        self.account = any_organisation_account(organisation=self.organisation)
        self.invoice = any_invoice(account=self.account, invoice_number="INV-0001")

        self.organisation_membership = OrganisationMembership.objects.create(
            organisation=self.organisation,
            membership_option=membership_option,
            created_datetime=start,
            start_date=start.date(),
            invoice=self.invoice,
        )

        self.client.force_login(self.user)

        self.url = f"/users/organisations/view/{self.organisation.pk}/"

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

        self.organisation_member.is_admin = True
        self.organisation_member.save()

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
        self.assertTemplateUsed(response, "organisation_view.html")

    def test_should_show_expected_members_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["name", "email", "status", "join_date", "role", "actions"]
        columns = [column.name for column in response.context["tables"][0].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_members_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Name", "Email", "Status", "Join Date", "Role", "Actions"]
        headings = [column.header for column in response.context["tables"][0].columns]
        self.assertListEqual(expected_headings, headings)

    def test_should_show_expected_organisation_members(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        expected_rows = [
            [
                self.organisation_member.user.get_full_name(),
                self.organisation_member.user.email,
                "Active",
                date_format(
                    timezone.localtime(self.organisation_member.accepted_datetime).date(), format="SHORT_DATE_FORMAT"
                ),
                "Member",
                "Remove,Make an Admin",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_expected_row_for_organisation_admin(self) -> None:
        # Given
        self.organisation_member.is_admin = True
        self.organisation_member.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        expected_rows = [
            [
                self.organisation_member.user.get_full_name(),
                self.organisation_member.user.email,
                "Active",
                date_format(
                    timezone.localtime(self.organisation_member.accepted_datetime).date(), format="SHORT_DATE_FORMAT"
                ),
                "Admin",
                "Remove,Revoke Admin Status",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_non_accepted_invite_as_invited(self) -> None:
        # Given
        self.organisation_member.accepted_datetime = None
        self.organisation_member.save()

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 0)

        expected_rows = [
            [
                self.organisation_member.user.get_full_name(),
                self.organisation_member.user.email,
                "Invited",
                "—",
                "",
                "Remove",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_remove_organisation_member(self) -> None:
        # When
        response = self.client.post(
            self.url, {"action": "remove_organisation_member", "organisation_member_id": self.organisation_member.pk}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?member_removed=true", response.url)

        with self.assertRaises(OrganisationMember.DoesNotExist):
            self.organisation_member.refresh_from_db()

    def test_should_make_organisation_member_admin(self) -> None:
        # When
        response = self.client.post(
            self.url, {"action": "make_organisation_admin", "organisation_member_id": self.organisation_member.pk}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?made_admin=true", response.url)

        self.organisation_member.refresh_from_db()
        self.assertEqual(self.organisation_member.is_admin, True)

    def test_should_not_make_non_active_member_organisation_admin(self) -> None:
        # Given
        self.organisation_member.accepted_datetime = None
        self.organisation_member.save()

        # When
        response = self.client.post(
            self.url, {"action": "make_organisation_admin", "organisation_member_id": self.organisation_member.pk}
        )

        # Then
        self.assertEqual(400, response.status_code)

        self.organisation_member.refresh_from_db()
        self.assertEqual(self.organisation_member.is_admin, False)

    def test_should_not_make_different_organisation_member_organisation_admin(self) -> None:
        # Given
        self.organisation_member.organisation = Organisation.objects.create(
            type=OrganisationType.objects.get(),
            name="Other Organisation",
            telephone="555-54321",
            contact_name="Jane Smith",
            email="jane@example.com",
            street_address="124 Main Street",
            suburb="",
            city="Capital City",
            postal_code="8080",
            postal_address="PO BOX 12345\nCapital City 8082",
        )
        self.organisation_member.save()

        # When
        response = self.client.post(
            self.url, {"action": "make_organisation_admin", "organisation_member_id": self.organisation_member.pk}
        )

        # Then
        self.assertEqual(400, response.status_code)

        self.organisation_member.refresh_from_db()
        self.assertEqual(self.organisation_member.is_admin, False)

    def test_should_revoke_organisation_member_admin(self) -> None:
        # Given
        self.organisation_member.is_admin = True
        self.organisation_member.save()

        # When
        response = self.client.post(
            self.url, {"action": "revoke_organisation_admin", "organisation_member_id": self.organisation_member.pk}
        )

        # Then
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"{self.url}?revoked_admin=true", response.url)

        self.organisation_member.refresh_from_db()
        self.assertEqual(self.organisation_member.is_admin, False)

    def test_should_show_expected_membership_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["membership", "duration", "status", "start_date", "expiry_date", "invoice", "actions"]
        columns = [column.name for column in response.context["tables"][1].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_membership_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Membership", "Duration", "Status", "Start Date", "Expires Date", "Invoice", "Actions"]
        columns = [column.header for column in response.context["tables"][1].columns]
        self.assertListEqual(expected_headings, columns)

    def test_should_show_expected_organisation_memberships(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 1)

        expected_rows = [
            [
                self.organisation_membership.membership_option.name,
                "1 month",
                "Active",
                date_format(self.organisation_membership.start_date, format="SHORT_DATE_FORMAT"),
                date_format(
                    self.organisation_membership.start_date + self.organisation_membership.membership_option.duration,
                    format="SHORT_DATE_FORMAT",
                ),
                self.organisation_membership.invoice.invoice_number,
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)

    def test_should_show_expected_invoice_columns(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_columns = ["invoice_number", "issue_date", "due_date", "amount", "paid", "due", "actions"]
        columns = [column.name for column in response.context["tables"][2].columns]
        self.assertListEqual(expected_columns, columns)

    def test_should_show_expected_invoice_headings(self) -> None:
        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        expected_headings = ["Invoice Number", "Issue Date", "Due Date", "Amount", "Paid", "Due", "Actions"]
        headings = [column.header for column in response.context["tables"][2].columns]
        self.assertListEqual(expected_headings, headings)

    def test_should_show_expected_invoices(self) -> None:
        # Given
        any_invoice(account=any_organisation_account())

        # When
        response = self.client.get(self.url)

        # Then
        self.assertEqual(200, response.status_code)

        rows = parse_response_table_rows(response, 2)

        self.maxDiff = None

        expected_rows = [
            [
                self.invoice.invoice_number,
                date_format(self.invoice.issue_date, format="SHORT_DATE_FORMAT"),
                date_format(self.invoice.due_date, format="SHORT_DATE_FORMAT"),
                self.invoice.amount,
                self.invoice.paid,
                self.invoice.due,
                "",
            ]
        ]

        self.assertListEqual(expected_rows, rows)
