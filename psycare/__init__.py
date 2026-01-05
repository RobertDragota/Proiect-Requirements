from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from .extensions import csrf, db, login_manager
from .models import User


def create_app(test_config: dict | None = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "ui"),
        static_url_path="/static",
    )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{Path(app.instance_path) / 'app.db'}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ALLOW_THERAPIST_REGISTER=os.environ.get("ALLOW_THERAPIST_REGISTER", "0") == "1",
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.patient import bp as patient_bp
    from .routes.therapist import bp as therapist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(therapist_bp)

    return app
