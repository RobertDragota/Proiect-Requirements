from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, RegisterForm
from ..models import User


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    return render_template("auth/login.html", form=form, title="Login")


@bp.post("/login")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("auth/login.html", form=form, title="Login"), 400

    user = User.query.filter_by(email=form.email.data.lower().strip()).first()
    if not user or not user.check_password(form.password.data):
        flash("Invalid email or password", "danger")
        return render_template("auth/login.html", form=form, title="Login"), 401

    login_user(user)
    next_url = request.args.get("next")
    return redirect(next_url or url_for("main.index"))


@bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterForm()
    return render_template("auth/register.html", form=form, title="Register")


@bp.post("/register")
def register_post():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template("auth/register.html", form=form, title="Register"), 400

    email = form.email.data.lower().strip()
    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("Email already registered", "warning")
        return render_template("auth/register.html", form=form, title="Register"), 409

    user = User(
        email=email,
        display_name=form.display_name.data.strip(),
        role="patient",
    )
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return redirect(url_for("main.index"))


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
