import pytest

from psycare import create_app
from psycare.extensions import db
from psycare.models import JournalEntry, PatientTherapist, User


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "test",
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        therapist = User(email="t@example.com", display_name="Therapist", role="therapist")
        therapist.set_password("Password123!")
        patient = User(email="p@example.com", display_name="Patient", role="patient")
        patient.set_password("Password123!")
        db.session.add_all([therapist, patient])
        db.session.commit()

        link = PatientTherapist(patient_id=patient.id, therapist_id=therapist.id)
        db.session.add(link)
        db.session.commit()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=False)


def test_register_login_logout_flow(client):
    r = client.post(
        "/auth/register",
        data={
            "email": "new@example.com",
            "display_name": "New User",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)

    r = client.post("/auth/logout", follow_redirects=False)
    assert r.status_code in (302, 303)

    r = login(client, "new@example.com", "Password123!")
    assert r.status_code in (302, 303)


def test_patient_journal_crud(client, app):
    r = login(client, "p@example.com", "Password123!")
    assert r.status_code in (302, 303)

    r = client.post(
        "/patient/journal/new",
        data={"title": "Day 1", "body": "Hello", "shared_with_therapist": "y"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)

    with app.app_context():
        patient = User.query.filter_by(email="p@example.com").first()
        entry = JournalEntry.query.filter_by(patient_id=patient.id).first()
        assert entry is not None
        entry_id = entry.id

    r = client.post(
        f"/patient/journal/{entry_id}/edit",
        data={"title": "Day 1 updated", "body": "Hello again", "shared_with_therapist": "y"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)

    r = client.post(f"/patient/journal/{entry_id}/delete", follow_redirects=False)
    assert r.status_code in (302, 303)


def test_therapist_cannot_see_unshared_journal(client, app):
    with app.app_context():
        patient = User.query.filter_by(email="p@example.com").first()
        entry = JournalEntry(patient_id=patient.id, title="Private", body="Secret", shared_with_therapist=False)
        db.session.add(entry)
        db.session.commit()

    r = login(client, "t@example.com", "Password123!")
    assert r.status_code in (302, 303)

    with app.app_context():
        patient = User.query.filter_by(email="p@example.com").first()
        pid = patient.id

    page = client.get(f"/therapist/patients/{pid}/journal")
    assert page.status_code == 200
    assert b"Secret" not in page.data


def test_rbac_blocks_wrong_role(client):
    login(client, "p@example.com", "Password123!")
    r = client.get("/therapist/dashboard")
    assert r.status_code in (403, 302)
