from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from ..authz import role_required
from ..extensions import db
from ..forms import AssignPatientForm, ResourceForm
from ..models import Alert, JournalEntry, MoodEntry, PatientTherapist, Resource, User


bp = Blueprint("therapist", __name__, url_prefix="/therapist")


def _assigned_patient_ids() -> list[int]:
    links = PatientTherapist.query.filter_by(therapist_id=current_user.id).all()
    return [l.patient_id for l in links]


@bp.get("/dashboard")
@role_required("therapist")
def dashboard():
    patient_ids = _assigned_patient_ids()

    patients = []
    if patient_ids:
        patients = User.query.filter(User.id.in_(patient_ids)).order_by(User.display_name.asc()).all()

    recent_journals = []
    if patient_ids:
        recent_journals = (
            JournalEntry.query.filter(
                JournalEntry.patient_id.in_(patient_ids),
                JournalEntry.shared_with_therapist.is_(True),
            )
            .order_by(JournalEntry.created_at.desc())
            .limit(10)
            .all()
        )

    recent_moods = []
    if patient_ids:
        recent_moods = (
            MoodEntry.query.filter(MoodEntry.patient_id.in_(patient_ids))
            .order_by(MoodEntry.created_at.desc())
            .limit(10)
            .all()
        )

    alerts = (
        Alert.query.filter_by(therapist_id=current_user.id, resolved=False)
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "therapist/dashboard.html",
        title="Therapist Dashboard",
        patients=patients,
        recent_journals=recent_journals,
        recent_moods=recent_moods,
        alerts=alerts,
    )


@bp.route("/patients", methods=["GET", "POST"])
@role_required("therapist")
def patients():
    form = AssignPatientForm()

    if form.validate_on_submit():
        email = form.patient_email.data.lower().strip()
        patient = User.query.filter_by(email=email).first()
        if not patient or patient.role != "patient":
            flash("Patient not found", "warning")
            return redirect(url_for("therapist.patients"))

        link = PatientTherapist(patient_id=patient.id, therapist_id=current_user.id)
        db.session.add(link)
        try:
            db.session.commit()
            flash("Patient linked", "success")
        except Exception:
            db.session.rollback()
            flash("This patient is already linked", "info")

        return redirect(url_for("therapist.patients"))

    patient_ids = _assigned_patient_ids()
    patients = []
    if patient_ids:
        patients = User.query.filter(User.id.in_(patient_ids)).order_by(User.display_name.asc()).all()

    return render_template("therapist/patients.html", title="My Patients", form=form, patients=patients)


@bp.get("/patients/<int:patient_id>/journal")
@role_required("therapist")
def patient_journal(patient_id: int):
    if patient_id not in _assigned_patient_ids():
        abort(403)

    patient = db.session.get(User, patient_id)
    if not patient:
        abort(404)

    entries = (
        JournalEntry.query.filter_by(patient_id=patient_id, shared_with_therapist=True)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )

    return render_template(
        "therapist/patient_journal.html",
        title=f"{patient.display_name} - Journal",
        patient=patient,
        entries=entries,
    )


@bp.get("/patients/<int:patient_id>/mood")
@role_required("therapist")
def patient_mood(patient_id: int):
    if patient_id not in _assigned_patient_ids():
        abort(403)

    patient = db.session.get(User, patient_id)
    if not patient:
        abort(404)

    entries = (
        MoodEntry.query.filter_by(patient_id=patient_id)
        .order_by(MoodEntry.created_at.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "therapist/patient_mood.html",
        title=f"{patient.display_name} - Mood",
        patient=patient,
        entries=entries,
    )


@bp.post("/alerts/<int:alert_id>/resolve")
@role_required("therapist")
def alert_resolve(alert_id: int):
    alert = db.session.get(Alert, alert_id)
    if not alert or alert.therapist_id != current_user.id:
        abort(404)

    alert.resolved = True
    db.session.commit()
    flash("Alert resolved", "success")
    return redirect(url_for("therapist.dashboard"))


@bp.get("/resources")
@role_required("therapist")
def resources_list():
    items = Resource.query.filter_by(therapist_id=current_user.id).order_by(Resource.created_at.desc()).all()
    return render_template("therapist/resources_list.html", title="Resources", items=items)


@bp.route("/resources/new", methods=["GET", "POST"])
@role_required("therapist")
def resources_new():
    form = ResourceForm()
    if form.validate_on_submit():
        item = Resource(
            therapist_id=current_user.id,
            title=form.title.data.strip(),
            url=form.url.data.strip(),
            description=(form.description.data or "").strip(),
        )
        db.session.add(item)
        db.session.commit()
        flash("Resource created", "success")
        return redirect(url_for("therapist.resources_list"))

    return render_template("therapist/resources_form.html", title="New Resource", form=form)


def _get_own_resource(resource_id: int) -> Resource:
    item = db.session.get(Resource, resource_id)
    if not item or item.therapist_id != current_user.id:
        abort(404)
    return item


@bp.route("/resources/<int:resource_id>/edit", methods=["GET", "POST"])
@role_required("therapist")
def resources_edit(resource_id: int):
    item = _get_own_resource(resource_id)
    form = ResourceForm(obj=item)
    if form.validate_on_submit():
        item.title = form.title.data.strip()
        item.url = form.url.data.strip()
        item.description = (form.description.data or "").strip()
        db.session.commit()
        flash("Resource updated", "success")
        return redirect(url_for("therapist.resources_list"))

    return render_template("therapist/resources_form.html", title="Edit Resource", form=form, item=item)


@bp.post("/resources/<int:resource_id>/delete")
@role_required("therapist")
def resources_delete(resource_id: int):
    item = _get_own_resource(resource_id)
    db.session.delete(item)
    db.session.commit()
    flash("Resource deleted", "success")
    return redirect(url_for("therapist.resources_list"))
