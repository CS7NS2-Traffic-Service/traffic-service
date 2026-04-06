from models.message import Message
from sqlalchemy.orm import Session


def list_messages(driver_id: str, db: Session) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.driver_id == driver_id)
        .order_by(Message.created_at.desc())
        .all()
    )


def mark_as_read(message_id: str, driver_id: str, db: Session) -> Message | None:
    message = (
        db.query(Message)
        .filter(
            Message.message_id == message_id,
            Message.driver_id == driver_id,
        )
        .first()
    )
    if message is None:
        return None
    message.is_read = True
    db.commit()
    db.refresh(message)
    return message


def create_message(
    driver_id: str,
    booking_id: str,
    content: str,
    db: Session,
) -> Message:
    new_message = Message(
        driver_id=driver_id,
        booking_id=booking_id,
        content=content,
    )
    db.add(new_message)
    db.flush()
    return new_message
