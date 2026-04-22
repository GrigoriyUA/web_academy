import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Reminder

DATABASE_URL = "sqlite:///notes.db"
POLL_INTERVAL = 60  # seconds

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def process_due_reminders() -> None:
    with Session(engine) as session:
        due = (
            session.query(Reminder)
            .filter(Reminder.remind_at <= datetime.utcnow(), Reminder.status == "pending")
            .all()
        )
        if not due:
            logger.info("No due reminders")
            return

        for reminder in due:
            # тут надсилається сповіщення (email, Telegram, тощо)
            logger.info("Sending reminder id=%d note_id=%d", reminder.id, reminder.note_id)
            reminder.status = "sent"

        session.commit()
        logger.info("Processed %d reminder(s)", len(due))


async def reminder_worker() -> None:
    while True:
        try:
            process_due_reminders()
        except Exception:
            logger.exception("Worker error")
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(reminder_worker())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
