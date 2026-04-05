import logging
import time

from database import SessionLocal
from domain import BookingStatus, utcnow
from events import publish_event
from models.booking import Booking

logger = logging.getLogger(__name__)

POLL_INTERVAL = 30


def run_expiry_loop() -> None:
    logger.info('Booking expiry loop started (every %ds)', POLL_INTERVAL)
    while True:
        try:
            db = SessionLocal()
            try:
                now = utcnow()
                expired = (
                    db.query(Booking)
                    .filter(
                        Booking.departure_time < now,
                        Booking.status.in_(
                            [BookingStatus.PENDING.value, BookingStatus.APPROVED.value]
                        ),
                    )
                    .all()
                )
                if expired:
                    for booking in expired:
                        booking.status = BookingStatus.EXPIRED.value
                    db.commit()

                    for booking in expired:
                        publish_event(
                            'booking.updated',
                            {
                                'booking_id': str(booking.booking_id),
                                'driver_id': str(booking.driver_id),
                                'status': BookingStatus.EXPIRED.value,
                            },
                        )
                        logger.info('Expired booking %s', booking.booking_id)
            finally:
                db.close()
        except Exception:
            logger.exception('Expiry loop error')
        time.sleep(POLL_INTERVAL)
