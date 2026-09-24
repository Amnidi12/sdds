"""
Notification service.

Provides a single create_notification() function used by all other service
layers to fire notifications on key lifecycle transitions.  The function is
designed to be fire-and-forget: it never raises on failure (notifications
are important but must not block the primary transaction).
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import Notification

logger = logging.getLogger("app.notifications")


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    body: str | None = None,
    event_type: str,
    link: str | None = None,
) -> Notification | None:
    """Create a notification for a specific user.

    This is called inside an already-open transaction managed by the caller,
    so we do NOT commit here — the caller's commit will persist the
    notification together with the rest of the operation (atomicity).
    """
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            event_type=event_type,
            link=link,
        )
        db.add(notification)
        await db.flush()
        return notification
    except Exception:
        logger.exception("Failed to create notification for user %s", user_id)
        return None
