import os
from dotenv import load_dotenv
from flask import Flask, render_template, get_flashed_messages, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, Length, URL

from .repo import DatabaseRepository
from .url_service import UrlService

# Load environment variables from .env file
load_dotenv_status = load_dotenv(override=True)

# Constants
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")


# Flask Configuration and Initialization
app = Flask(__name__)
app.secret_key = SECRET_KEY
service = UrlService(repo=DatabaseRepository(conn_str=DATABASE_URL))


# Form Definitions
class UrlInputForm(FlaskForm):
    url = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=4, max=255),
            URL(allow_ip=True, message="Некорректный URL"),
        ],
    )


# Routes
@app.route("/", methods=["GET"])
def main():
    form = UrlInputForm()
    messages = get_flashed_messages(with_categories=True)
    return render_template("main.html", messages=messages, form=form)


@app.route("/urls", methods=["GET"])
def urls_get():
    basic_url_data = service.fetch_basic_url_data()
    basic_url_dict = {url[0]: url[1] for url in basic_url_data}
    latest_checks_data = service.fetch_latest_checks()
    latest_checks_dict = {
        check[0]: {"date": check[1], "status_code": check[2]}
        for check in latest_checks_data
    }
    url_data = []
    for url_id, url_name in basic_url_dict.items():
        latest_check = latest_checks_dict.get(url_id)
        if latest_check:
            url_data.append(
                {
                    "url_id": url_id,
                    "url_name": url_name,
                    "latest_check_date": latest_check["date"],
                    "status_code": latest_check["status_code"],
                }
            )
    return render_template("urls.html", url_data=url_data)


@app.route("/urls", methods=["POST"])
def urls_post():
    form = UrlInputForm()
    if form.validate_on_submit():
        return _handle_valid_form_submission(form)
    return _handle_invalid_form_submission(form)


@app.route("/urls/<int:url_id>", methods=["GET"])
def get_url_by_id(url_id):
    url_checks = service.get_url_checks(url_id)
    url_data = service.get_url_data(url_id)

    if not url_data:
        flash("URL not found.", "info")
        return redirect(url_for("main"))

    url_id, url_name, created_at = url_data
    created_at = created_at.date()

    return render_template(
        "url.html",
        url_id=url_id,
        url_name=url_name,
        created_at=created_at,
        checks=url_checks,
    )


@app.route("/urls/<int:url_id>/checks", methods=["POST"])
def post_url_checks(url_id):
    check_results = service.fetch_and_store_web_content(url_id=url_id)
    if "error" in check_results:
        flash("Произошла ошибка при проверке", "danger")
    else:
        flash("Страница успешно проверена", "info")
    return redirect(url_for("get_url_by_id", url_id=url_id))


# Helper Functions


def _handle_valid_form_submission(form):
    url = service.parse_and_serialize_form(form.data.get("url"))
    url_id = service.get_id_url_if_exists(url)
    if url_id:
        flash("Страница уже существует", "info")
    else:
        url_id = service.insert_url_and_return_id(url)
        flash("Страница успешно добавлена", "success")
    return redirect(url_for("get_url_by_id", url_id=url_id))


def _handle_invalid_form_submission(form):
    for _, errors in form.errors.items():
        for error in errors:
            flash(error, "danger")
    return render_template("main.html", form=form), 422
