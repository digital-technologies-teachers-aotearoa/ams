"""Enqueue tasks for Xero billing operations."""

import logging

from django_q.tasks import async_task

logger = logging.getLogger(__name__)


def enqueue_invoice_update_task(webhook_id: str | None = None) -> str:
    """Enqueue an async task to fetch invoice updates.

    Args:
        webhook_id: Optional webhook ID for correlated logging.

    Returns:
        Task ID string that can be used to track task execution.
    """
    log_prefix = f"[{webhook_id}] " if webhook_id else ""

    task_id = async_task(
        "ams.billing.providers.xero.tasks.process_tasks.process_invoice_updates_task",
        webhook_id=webhook_id,
        task_name=f"xero_invoice_update_{webhook_id}"
        if webhook_id
        else "xero_invoice_update",
        group="xero_webhooks",
        timeout=60,
    )

    logger.info(
        "%sEnqueued invoice update task (task_id=%s)",
        log_prefix,
        task_id,
    )

    return task_id
