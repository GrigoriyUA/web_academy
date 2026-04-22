from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ReminderCreate(BaseModel):
    remind_at: datetime

    @field_validator("remind_at")
    @classmethod
    def remind_at_must_be_future(cls, v: datetime) -> datetime:
        if v <= datetime.utcnow():
            raise ValueError("remind_at must be in the future")
        return v


class NoteCreate(BaseModel):
    user_id: int
    title: str
    content: Optional[str] = None
    reminder: Optional[ReminderCreate] = None


class ReminderRead(BaseModel):
    id: int
    remind_at: datetime

    model_config = {"from_attributes": True}

та
class NoteRead(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str]
    is_archived: bool
    created_at: datetime
    reminder: Optional[ReminderRead]

    model_config = {"from_attributes": True}
