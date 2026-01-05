"""Membership-related billing orchestration.

Separated from models to avoid circular imports. Uses TYPE_CHECKING for
model type annotations and performs runtime-safe operations.
"""

from __future__ import annotations

import logging
import re
from functools import partial
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from ams.billing.exceptions import BillingDetailUpdateError
from ams.billing.exceptions import BillingInvoiceError
from ams.billing.services import BillingService
from ams.billing.services import get_billing_service
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipStatus

if TYPE_CHECKING:  # pragma: no cover
    from decimal import Decimal

    from ams.billing.models import Account
    from ams.billing.models import Invoice

logger = logging.getLogger(__name__)


class MembershipBillingService:
    """Service class to handle billing operations related to memberships."""

    def __init__(self, billing_service: BillingService | None = None):
        self.billing_service = billing_service or get_billing_service()

    def can_send_email(self, email: str) -> bool:
        """Check if emails can be sent to this address based on whitelist."""
        return bool(
            not settings.BILLING_EMAIL_WHITELIST_REGEX
            or re.search(settings.BILLING_EMAIL_WHITELIST_REGEX, email),
        )

    def create_membership_invoice(
        self,
        account: Account,
        membership_option: MembershipOption,
        seat_count: int = 1,
        membership=None,
        unit_price_override: Decimal | None = None,
    ) -> Invoice | None:
        """Create an invoice for a membership option if billable.

        Args:
            account: The billing account for the invoice.
            membership_option: The membership option being invoiced.
            seat_count: Number of seats/quantity for the membership (default: 1).
            membership: Optional IndividualMembership or OrganisationMembership to link.
            unit_price_override: Optional override for unit price (e.g., pro-rata).

        Raises:
            BillingDetailUpdateError: If billing details update fails.
            BillingInvoiceError: If invoice creation fails.
        """
        if not self.billing_service:
            logger.info("No billing service configured; skipping invoice creation")
            return None

        if membership_option.cost == 0:
            logger.info(
                "Membership option %s is free; skipping invoice creation",
                membership_option.name,
            )
            return None

        try:
            if account.user_id:
                email = account.user.email
                self.billing_service.update_user_billing_details(account.user)
            else:
                email = account.organisation.email
                self.billing_service.update_organisation_billing_details(
                    account.organisation,
                )
        except Exception as e:  # broad to wrap in domain error
            logger.exception(
                "Error updating account %s billing details",
                account.pk,
            )
            raise BillingDetailUpdateError(e) from e

        try:
            invoice_line_items = [
                {
                    "description": str(membership_option),
                    "unit_amount": unit_price_override or membership_option.cost,
                    "quantity": seat_count,
                },
            ]
            issue_date = timezone.localdate()
            due_date = issue_date + timezone.timedelta(
                days=membership_option.invoice_due_days,
            )

            invoice = self.billing_service.create_invoice(
                account,
                issue_date,
                due_date,
                invoice_line_items,
                membership_option.invoice_reference,
            )

            # Link invoice to membership
            if membership:
                if hasattr(membership, "user"):
                    # Individual membership
                    invoice.individual_membership = membership
                    invoice.save(update_fields=["individual_membership"])
                else:
                    # Organisation membership
                    invoice.organisation_membership = membership
                    invoice.save(update_fields=["organisation_membership"])

            if self.can_send_email(email):
                transaction.on_commit(partial(self._email_invoice, invoice=invoice))

            logger.info(
                "Created invoice %s for account %s",
                invoice.invoice_number,
                account.pk,
            )
        except Exception as e:  # broad to wrap in domain error
            logger.exception(
                "Error creating invoice for account %s",
                account.pk,
            )
            raise BillingInvoiceError(e) from e
        else:
            return invoice

    def _email_invoice(self, invoice: Invoice) -> None:
        """Send invoice email via billing service."""
        try:
            self.billing_service.email_invoice(invoice)
            logger.info("Sent email for invoice %s", invoice.invoice_number)
        except Exception:  # broad but logs traceback
            logger.exception(
                "Failed to send email for invoice %s",
                invoice.invoice_number,
            )

    def approve_paid_memberships(self, invoice: Invoice) -> None:
        """Approve memberships when invoice is paid.

        Handles both individual and organisation memberships.
        """
        if not invoice.paid_date:
            return

        # Approve individual membership if linked
        if invoice.individual_membership:
            if invoice.individual_membership.status() == MembershipStatus.PENDING:
                invoice.individual_membership.approved_datetime = timezone.now()
                invoice.individual_membership.save(update_fields=["approved_datetime"])
                logger.info(
                    "Approved individual membership %s for invoice %s",
                    invoice.individual_membership.pk,
                    invoice.invoice_number,
                )

        # Approve organisation membership if linked
        if invoice.organisation_membership:
            if invoice.organisation_membership.status() == MembershipStatus.PENDING:
                invoice.organisation_membership.approved_datetime = timezone.now()
                invoice.organisation_membership.save(
                    update_fields=["approved_datetime"],
                )
                logger.info(
                    "Approved organisation membership %s for invoice %s",
                    invoice.organisation_membership.pk,
                    invoice.invoice_number,
                )
