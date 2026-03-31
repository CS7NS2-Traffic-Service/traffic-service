import logging
import time
from datetime import datetime, timezone

from database import SessionLocal
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
                expired = (
                    db.query(Booking)
                    .filter(
                        Booking.departure_time < datetime.now(timezone.utc),
                        Booking.status.in_(['PENDING', 'APPROVED']),
                    )
                    .all()
                )
                for booking in expired:
                    booking.status = 'EXPIRED'
                    db.commit()

                    publish_event(
                        'booking.updated',
                        {
                            'booking_id': str(booking.booking_id),
                            'driver_id': str(booking.driver_id),
                            'status': 'EXPIRED',
                        },
                    )
                    logger.info('Expired booking %s', booking.booking_id)
            finally:
                db.close()
        except Exception:
            logger.exception('Expiry loop error')
        time.sleep(POLL_INTERVAL)
