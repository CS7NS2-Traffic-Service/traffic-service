from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum


class BookingStatus(StrEnum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    CANCELLED = 'CANCELLED'
    EXPIRED = 'EXPIRED'


ALLOWED_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {
        BookingStatus.APPROVED,
        BookingStatus.REJECTED,
        BookingStatus.EXPIRED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.APPROVED: {BookingStatus.CANCELLED, BookingStatus.EXPIRED},
    BookingStatus.REJECTED: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.EXPIRED: set(),
}


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_status(raw: str) -> BookingStatus:
    return BookingStatus(raw)


def transition(current: BookingStatus, target: BookingStatus) -> BookingStatus:
    if target == current:
        return current
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f'Invalid transition {current} -> {target}')
    return target
