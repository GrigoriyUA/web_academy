from enum import Enum, auto
from functools import wraps
from typing import Callable


class Role(Enum):
    USER = auto()
    ADMIN = auto()
    SERVICE = auto()  # обходить всі перевірки


PERMISSIONS: dict[str, set[Role]] = {
    "read_own_notes":   {Role.USER, Role.ADMIN, Role.SERVICE},
    "read_all_notes":   {Role.ADMIN, Role.SERVICE},
    "create_note":      {Role.USER, Role.ADMIN, Role.SERVICE},
    "delete_note":      {Role.ADMIN, Role.SERVICE},
    "manage_users":     {Role.ADMIN, Role.SERVICE},
}


class AccessDenied(Exception):
    pass


class Principal:
    def __init__(self, user_id: int, role: Role):
        self.user_id = user_id
        self.role = role

    def can(self, permission: str) -> bool:
        # SERVICE обходить всі перевірки (аналог BYPASSRLS)
        if self.role == Role.SERVICE:
            return True
        return self.role in PERMISSIONS.get(permission, set())

    def require(self, permission: str) -> None:
        if not self.can(permission):
            raise AccessDenied(
                f"Role '{self.role.name}' lacks permission '{permission}'"
            )


def require_permission(permission: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(self, principal: Principal, *args, **kwargs):
            principal.require(permission)
            return fn(self, principal, *args, **kwargs)
        return wrapper
    return decorator


# --- Демонстрація з реальною БД ---

from sqlalchemy.orm import Session
from models import Note


class SecureNoteRepository:
    def __init__(self, session: Session):
        self.session = session

    @require_permission("read_own_notes")
    def get_my_notes(self, principal: Principal) -> list[Note]:
        query = self.session.query(Note)
        if principal.role == Role.USER:
            query = query.filter(Note.user_id == principal.user_id)
        return query.all()

    @require_permission("delete_note")
    def delete_note(self, principal: Principal, note_id: int) -> bool:
        note = self.session.get(Note, note_id)
        if not note:
            return False
        self.session.delete(note)
        self.session.commit()
        return True
