from __future__ import annotations

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user


bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "therapist":
            return redirect(url_for("therapist.dashboard"))
        return redirect(url_for("patient.dashboard"))

    return render_template("index.html", title="Home")


@bp.get("/health")
def health():
    return {"status": "ok"}, 200
