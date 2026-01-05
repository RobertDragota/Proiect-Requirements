from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from ..authz import role_required
from ..extensions import db
from ..forms import JournalForm, MoodForm
from ..models import Alert, JournalEntry, MoodEntry, PatientTherapist


bp = Blueprint("patient", __name__, url_prefix="/patient")


@bp.get("/dashboard")
@role_required("patient")
def dashboard():
    journal_entries = (
        JournalEntry.query.filter_by(patient_id=current_user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(5)
        .all()
    )
    mood_entries = (
        MoodEntry.query.filter_by(patient_id=current_user.id)
        .order_by(MoodEntry.created_at.desc())
        .limit(10)
        .all()
    )
    therapist_link = PatientTherapist.query.filter_by(patient_id=current_user.id).first()
    return render_template(
        "patient/dashboard.html",
        title="Patient Dashboard",
        journal_entries=journal_entries,
        mood_entries=mood_entries,
        therapist_link=therapist_link,
    )


@bp.route("/journal", methods=["GET"])
@role_required("patient")
def journal_list():
    entries = (
        JournalEntry.query.filter_by(patient_id=current_user.id)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )
    return render_template("patient/journal_list.html", title="My Journal", entries=entries)


@bp.route("/journal/new", methods=["GET", "POST"])
@role_required("patient")
def journal_new():
    form = JournalForm()
    if form.validate_on_submit():
        entry = JournalEntry(
            patient_id=current_user.id,
            title=form.title.data.strip(),
            body=form.body.data.strip(),
            shared_with_therapist=bool(form.shared_with_therapist.data),
            flagged_risk=bool(form.flagged_risk.data),
        )
        db.session.add(entry)
        db.session.commit()
        flash("Journal entry created", "success")
        return redirect(url_for("patient.journal_list"))

    return render_template("patient/journal_form.html", title="New Entry", form=form)


def _get_own_entry(entry_id: int) -> JournalEntry:
    entry = db.session.get(JournalEntry, entry_id)
    if not entry or entry.patient_id != current_user.id:
        abort(404)
    return entry


@bp.route("/journal/<int:entry_id>/edit", methods=["GET", "POST"])
@role_required("patient")
def journal_edit(entry_id: int):
    entry = _get_own_entry(entry_id)
    form = JournalForm(obj=entry)
    if form.validate_on_submit():
        entry.title = form.title.data.strip()
        entry.body = form.body.data.strip()
        entry.shared_with_therapist = bool(form.shared_with_therapist.data)
        entry.flagged_risk = bool(form.flagged_risk.data)
        db.session.commit()
        flash("Journal entry updated", "success")
        return redirect(url_for("patient.journal_list"))

    return render_template("patient/journal_form.html", title="Edit Entry", form=form, entry=entry)


@bp.post("/journal/<int:entry_id>/delete")
@role_required("patient")
def journal_delete(entry_id: int):
    entry = _get_own_entry(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("Journal entry deleted", "success")
    return redirect(url_for("patient.journal_list"))


@bp.route("/mood", methods=["GET", "POST"])
@role_required("patient")
def mood_checkin():
    form = MoodForm()
    if form.validate_on_submit():
        entry = MoodEntry(
            patient_id=current_user.id,
            rating=form.rating.data,
            note=(form.note.data or "").strip(),
        )
        db.session.add(entry)
        db.session.commit()
        flash("Mood check-in saved", "success")
        return redirect(url_for("patient.dashboard"))

    recent = (
        MoodEntry.query.filter_by(patient_id=current_user.id)
        .order_by(MoodEntry.created_at.desc())
        .limit(30)
        .all()
    )
    return render_template("patient/mood.html", title="Mood Check-in", form=form, recent=recent)


@bp.get("/resources")
@role_required("patient")
def resources():
    therapist_link = PatientTherapist.query.filter_by(patient_id=current_user.id).first()
    if not therapist_link:
        items = []
    else:
        from ..models import Resource

        items = (
            Resource.query.filter_by(therapist_id=therapist_link.therapist_id)
            .order_by(Resource.created_at.desc())
            .all()
        )
    return render_template("patient/resources.html", title="Resources", items=items)


@bp.route("/crisis", methods=["GET", "POST"])
@role_required("patient")
def crisis():
    therapist_link = PatientTherapist.query.filter_by(patient_id=current_user.id).first()

    from flask import request

    if request.method == "POST":
        alert = Alert(
            patient_id=current_user.id,
            therapist_id=therapist_link.therapist_id if therapist_link else None,
            kind="panic",
            message="Patient pressed the panic button.",
        )
        db.session.add(alert)
        db.session.commit()
        flash("Alert sent to your therapist (if linked).", "warning")
        return redirect(url_for("patient.dashboard"))

    return render_template(
        "patient/crisis.html",
        title="Crisis / Emergency",
        therapist_link=therapist_link,
    )
