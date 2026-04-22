from datetime import datetime
from sqlalchemy import Column, Index, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False)

    notes = relationship("Note", back_populates="owner")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="notes")
    reminder = relationship("Reminder", back_populates="note", uselist=False)

    __table_args__ = (
        Index("ix_notes_title", "title"),
        Index("ix_notes_created_at", "created_at"),
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), unique=True)
    remind_at = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")

    note = relationship("Note", back_populates="reminder")
