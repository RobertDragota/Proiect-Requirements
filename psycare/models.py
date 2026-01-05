from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(255), nullable=False)
    role: str = db.Column(db.String(32), nullable=False, default="patient")  # patient|therapist
    display_name: str = db.Column(db.String(120), nullable=False, default="")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class PatientTherapist(db.Model):
    __tablename__ = "patient_therapists"

    id: int = db.Column(db.Integer, primary_key=True)
    patient_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    therapist_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("patient_id", "therapist_id", name="uq_patient_therapist"),
    )


class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id: int = db.Column(db.Integer, primary_key=True)
    patient_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title: str = db.Column(db.String(200), nullable=False)
    body: str = db.Column(db.Text, nullable=False)
    shared_with_therapist: bool = db.Column(db.Boolean, nullable=False, default=True)
    flagged_risk: bool = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class MoodEntry(db.Model):
    __tablename__ = "mood_entries"

    id: int = db.Column(db.Integer, primary_key=True)
    patient_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    rating: int = db.Column(db.Integer, nullable=False)  # 1..10
    note: str = db.Column(db.String(500), nullable=False, default="")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Alert(db.Model):
    __tablename__ = "alerts"

    id: int = db.Column(db.Integer, primary_key=True)
    patient_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    therapist_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    kind: str = db.Column(db.String(50), nullable=False, default="panic")
    message: str = db.Column(db.String(500), nullable=False, default="")
    resolved: bool = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Resource(db.Model):
    __tablename__ = "resources"

    id: int = db.Column(db.Integer, primary_key=True)
    therapist_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title: str = db.Column(db.String(200), nullable=False)
    url: str = db.Column(db.String(500), nullable=False)
    description: str = db.Column(db.String(500), nullable=False, default="")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
