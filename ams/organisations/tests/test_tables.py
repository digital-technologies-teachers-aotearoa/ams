"""Tests for organisation tables."""

from datetime import timedelta

import pytest
from django.template import Context
from django.template import Template
from django.utils import timezone

from ams.billing.tests.factories import AccountFactory
from ams.billing.tests.factories import InvoiceFactory
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tables import OrganisationMembershipTable
from ams.organisations.tests.factories import OrganisationFactory

pytestmark = pytest.mark.django_db


class TestOrganisationMembershipTable:
    """Tests for OrganisationMembershipTable invoice column configuration."""

    def test_invoice_column_uses_template_column(self):
        """Test that invoice column is configured to use TemplateColumn."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Check that invoice column is using the correct template
        invoice_column = table.base_columns["invoice"]
        assert invoice_column.template_name == "users/tables/invoice_column.html"

    def test_invoice_column_with_no_invoice(self):
        """Test that invoice column has None when there's no invoice."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct data
        assert len(table.data) == 1
        assert not table.data[0].invoices.exists()

    def test_invoice_column_with_paid_invoice_and_xero(self):
        """Test that invoice data is available for paid invoice with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="XERO-123",
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoices.first() == invoice
        assert table.data[0].invoices.first().billing_service_invoice_id == "XERO-123"
        assert table.data[0].invoices.first().paid_date is not None

    def test_invoice_column_with_paid_invoice_no_xero(self):
        """Test that invoice data is available for paid invoice without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="",  # No Xero integration
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoices.first() == invoice
        assert table.data[0].invoices.first().billing_service_invoice_id == ""
        assert table.data[0].invoices.first().paid_date is not None

    def test_invoice_column_with_unpaid_invoice_and_xero(self):
        """Test that invoice data is available for unpaid invoice with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=None,
            billing_service_invoice_id="XERO-123",
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoices.first() == invoice
        assert table.data[0].invoices.first().billing_service_invoice_id == "XERO-123"
        assert table.data[0].invoices.first().paid_date is None

    def test_invoice_column_with_unpaid_invoice_no_xero(self):
        """Test that invoice data is available for unpaid invoice without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=None,
            billing_service_invoice_id="",  # No Xero integration
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoices.first() == invoice
        assert table.data[0].invoices.first().billing_service_invoice_id == ""
        assert table.data[0].invoices.first().paid_date is None


class TestInvoiceColumnTemplateRendering:
    """Tests for the invoice column template rendering behavior."""

    def test_invoice_template_renders_not_required_when_no_invoice(self):
        """Test invoice template renders 'Not required' when there's no invoice."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"record": membership})

        html = template.render(context)

        assert "Not required" in html
        assert "text-secondary" in html

    def test_invoice_template_renders_paid_with_xero_link(self):
        """Test invoice template renders a link for paid invoices with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="XERO-123",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"record": membership})

        html = template.render(context)

        assert "Paid" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' in html
        assert "text-success" in html

    def test_invoice_template_renders_paid_without_xero_link(self):
        """Test invoice template renders text only for paid invoices without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"record": membership})

        html = template.render(context)

        assert "Paid" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' not in html
        assert "text-success" in html

    def test_invoice_template_renders_awaiting_payment_with_xero_link(self):
        """Test invoice template renders a link for unpaid invoices with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=None,
            billing_service_invoice_id="XERO-456",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"record": membership})

        html = template.render(context)

        assert "Awaiting payment" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' in html
        assert "text-warning" in html

    def test_invoice_template_renders_awaiting_payment_without_xero_link(self):
        """Test invoice template renders text only for unpaid invoices without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )
        invoice = InvoiceFactory(
            account=account,
            organisation_membership=membership,
            paid_date=None,
            billing_service_invoice_id="",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"record": membership})

        html = template.render(context)

        assert "Awaiting payment" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' not in html
        assert "text-warning" in html


class TestOrganisationMembershipTableActionsColumn:
    """Tests for the actions column on OrganisationMembershipTable."""

    def test_actions_column_exists(self):
        """Test that actions column is configured on the table."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        assert "actions" in table.base_columns

    def test_actions_column_renders_cancel_button_for_active_membership(self):
        """Test that actions column renders cancel button for active membership."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            active=True,
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" in html

    def test_actions_column_renders_cancel_button_for_pending_membership(self):
        """Test that actions column renders cancel button for pending membership."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            pending=True,
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" in html

    def test_actions_column_no_cancel_button_for_cancelled_membership(self):
        """Test that actions column does not render cancel button for cancelled
        membership."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            cancelled=True,
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" not in html

    def test_actions_column_no_cancel_button_for_expired_membership(self):
        """Test that actions column does not render cancel button for expired
        membership."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            expired=True,
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])
        html = table.render_actions(membership)

        assert "Cancel Membership" not in html
