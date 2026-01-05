from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import abort
from flask_login import current_user, login_required


F = TypeVar("F", bound=Callable)


def role_required(role: str) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not getattr(current_user, "is_authenticated", False):
                abort(401)
            if getattr(current_user, "role", None) != role:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
