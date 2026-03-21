from dependencies import get_db_connection
from fastapi import APIRouter, Depends, Header, HTTPException
from schemas import MessageListResponse, MessageResponse
from services.message import list_messages, mark_as_read
from sqlalchemy.orm import Session

router = APIRouter()


def _to_response(message) -> MessageResponse:
    return MessageResponse(
        message_id=str(message.message_id),
        driver_id=str(message.driver_id),
        booking_id=str(message.booking_id),
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at,
    )


@router.get('', status_code=200)
def list_all(
    x_driver_id: str = Header(...),
    db: Session = Depends(get_db_connection),
) -> MessageListResponse:
    messages = list_messages(x_driver_id, db)
    return MessageListResponse(messages=[_to_response(m) for m in messages])


@router.put('/{message_id}/read', status_code=200)
def mark_read(
    message_id: str,
    x_driver_id: str = Header(...),
    db: Session = Depends(get_db_connection),
) -> MessageResponse:
    message = mark_as_read(message_id, x_driver_id, db)
    if message is None:
        raise HTTPException(status_code=404, detail='Message not found')
    return _to_response(message)
