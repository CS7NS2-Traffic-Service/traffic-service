from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message_id: str
    driver_id: str
    booking_id: str
    content: str
    is_read: bool
    created_at: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
