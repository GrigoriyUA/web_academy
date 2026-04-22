from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models import Note, Reminder


class NoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_notes(self, user_id: int) -> list[Note]:
        return (
            self.session.query(Note)
            .filter(Note.user_id == user_id, Note.is_archived == False)
            .all()
        )

    def create_with_reminder(
        self, note_data: dict[str, Any], reminder_data: dict[str, Any]
    ) -> Note:
        with self.session.begin_nested():
            note = Note(**note_data)
            self.session.add(note)
            self.session.flush()

            reminder = Reminder(note_id=note.id, **reminder_data)
            self.session.add(reminder)

        return note
