from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, PasswordField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, URL


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    display_name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])


class JournalForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=200)])
    body = TextAreaField("Entry", validators=[DataRequired(), Length(min=2)])
    shared_with_therapist = BooleanField("Share with therapist", default=True)
    flagged_risk = BooleanField("Flag as urgent / risky", default=False)


class MoodForm(FlaskForm):
    rating = IntegerField("How do you feel today? (1-10)", validators=[DataRequired(), NumberRange(min=1, max=10)])
    note = StringField("Note (optional)", validators=[Optional(), Length(max=500)])


class ResourceForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2, max=200)])
    url = StringField("URL", validators=[DataRequired(), URL(), Length(max=500)])
    description = StringField("Description", validators=[Optional(), Length(max=500)])


class AssignPatientForm(FlaskForm):
    patient_email = StringField("Patient Email", validators=[DataRequired(), Email(), Length(max=255)])
