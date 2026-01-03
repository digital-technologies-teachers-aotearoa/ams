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
            invoice=None,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Check that invoice column is using the correct template
        invoice_column = table.base_columns["invoice"]
        assert invoice_column.template_name == "users/tables/invoice_column.html"
        assert invoice_column.accessor == "invoice"

    def test_invoice_column_with_no_invoice(self):
        """Test that invoice column has None when there's no invoice."""
        org = OrganisationFactory()
        membership = OrganisationMembershipFactory(
            organisation=org,
            invoice=None,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct data
        assert len(table.data) == 1
        assert table.data[0].invoice is None

    def test_invoice_column_with_paid_invoice_and_xero(self):
        """Test that invoice data is available for paid invoice with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="XERO-123",
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            invoice=invoice,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoice == invoice
        assert table.data[0].invoice.billing_service_invoice_id == "XERO-123"
        assert table.data[0].invoice.paid_date is not None

    def test_invoice_column_with_paid_invoice_no_xero(self):
        """Test that invoice data is available for paid invoice without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="",  # No Xero integration
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            invoice=invoice,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoice == invoice
        assert table.data[0].invoice.billing_service_invoice_id == ""
        assert table.data[0].invoice.paid_date is not None

    def test_invoice_column_with_unpaid_invoice_and_xero(self):
        """Test that invoice data is available for unpaid invoice with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=None,
            billing_service_invoice_id="XERO-123",
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            invoice=invoice,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoice == invoice
        assert table.data[0].invoice.billing_service_invoice_id == "XERO-123"
        assert table.data[0].invoice.paid_date is None

    def test_invoice_column_with_unpaid_invoice_no_xero(self):
        """Test that invoice data is available for unpaid invoice without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=None,
            billing_service_invoice_id="",  # No Xero integration
        )
        membership = OrganisationMembershipFactory(
            organisation=org,
            invoice=invoice,
            start_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=335),
            membership_option__type=MembershipOptionType.ORGANISATION,
        )

        table = OrganisationMembershipTable([membership])

        # Verify that the table has the correct invoice data
        assert len(table.data) == 1
        assert table.data[0].invoice == invoice
        assert table.data[0].invoice.billing_service_invoice_id == ""
        assert table.data[0].invoice.paid_date is None


class TestInvoiceColumnTemplateRendering:
    """Tests for the invoice column template rendering behavior."""

    def test_invoice_template_renders_not_required_when_no_invoice(self):
        """Test invoice template renders 'Not required' when there's no invoice."""
        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"value": None})

        html = template.render(context)

        assert "Not required" in html
        assert "text-secondary" in html

    def test_invoice_template_renders_paid_with_xero_link(self):
        """Test invoice template renders a link for paid invoices with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="XERO-123",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"value": invoice})

        html = template.render(context)

        assert "Paid" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' in html
        assert "text-success" in html

    def test_invoice_template_renders_paid_without_xero_link(self):
        """Test invoice template renders text only for paid invoices without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=timezone.localdate(),
            billing_service_invoice_id="",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"value": invoice})

        html = template.render(context)

        assert "Paid" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' not in html
        assert "text-success" in html

    def test_invoice_template_renders_awaiting_payment_with_xero_link(self):
        """Test invoice template renders a link for unpaid invoices with Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=None,
            billing_service_invoice_id="XERO-456",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"value": invoice})

        html = template.render(context)

        assert "Awaiting payment" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' in html
        assert "text-warning" in html

    def test_invoice_template_renders_awaiting_payment_without_xero_link(self):
        """Test invoice template renders text only for unpaid invoices without Xero."""
        org = OrganisationFactory()
        account = AccountFactory(organisation=org)
        invoice = InvoiceFactory(
            account=account,
            paid_date=None,
            billing_service_invoice_id="",
        )

        template = Template(
            "{% load icon %}{% include 'users/tables/invoice_column.html' %}",
        )
        context = Context({"value": invoice})

        html = template.render(context)

        assert "Awaiting payment" in html
        assert f'href="/billing/invoice/{invoice.invoice_number}/"' not in html
        assert "text-warning" in html
