from flask import (
    Flask,
    render_template,
    get_flashed_messages,
    flash,
    redirect,
    url_for,
    Response,
)


from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, Length, URL
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import logging
from .repo import DatabaseRepository
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s"
)
logging.info("Initializing application...")
load_dotenv_status = load_dotenv(override=True)
if load_dotenv_status:
    logging.info("Successfully loaded .env file.")
else:
    logging.error("Failed to load .env file.")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if app.secret_key:
    logging.info("Successfully loaded app.SECRET_KEY")
else:
    logging.error("failed to load app.SECRET_KEY")


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    logging.info("Database URL retrieved from environment variables.")
else:
    logging.error("Failed to retrieve DATABASE_URL from environment variables.")


class UrlInputForm(FlaskForm):
    name = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=4, max=255),
            URL(allow_ip=True, message="Некорректный URL"),
        ],
    )


def make_check(url):
    try:
        url_response = requests.get(url)
        content = url_response.text
        status_code = url_response.status_code
        soup = BeautifulSoup(content, "html.parser")

        h1 = soup.find("h1")
        h1 = h1.text.strip() if h1 else "Не найден"

        title = soup.title
        title = title.text.strip() if title else "Не найден"

        description = soup.find("meta", attrs={"name": "description"})
        description = (
            description.get("content", "").strip() if description else "Не найден"
        )

        logging.info(f"{url} was checked with status code {status_code}")
        return {
            "status_code": status_code,
            "h1": h1,
            "title": title,
            "description": description,
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Connection error while accessing {url}: {e}")
        return {"status_code": 500, "error": str(e)}


@app.route("/", methods=["GET"])
def main():
    logging.info("Received GET request on main endpoint.")
    form = UrlInputForm()
    messages = get_flashed_messages(with_categories=True)
    if messages:
        logging.info(f"Flashed messages: {messages}")
    return render_template("main.html", messages=messages, form=form)


@app.route("/urls", methods=["GET"])
def urls_get():
    logging.info("Received GET request on /urls endpoint.")
    with DatabaseRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.fetch_latest_url_data()
    logging.info(f"Retrieved {len(db_urls)} URL from the database.")
    logging.info(f"Variables for urls.html: db_urls={db_urls}")
    return render_template("urls.html", db_urls=db_urls)


@app.route("/urls", methods=["POST"])
def urls_post():
    logging.info("Received POST request on /urls endpoint.")
    form = UrlInputForm()
    full_url = form.data.get("name").lower()
    parsed_url = urlparse(full_url)
    netloc = parsed_url.netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    base_url = f"{parsed_url.scheme}://{netloc}"

    if not form.validate_on_submit():
        logging.warning(
            f"Form validation failed for URL: {base_url}. Errors: {form.errors}"
        )
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("main"))

    with DatabaseRepository(conn_str=DATABASE_URL) as repo:
        if repo.url_exists(base_url):
            logging.info(f"URL {base_url} already exists in the database.")
            url_id = repo.fetch_url_id(base_url)
            if url_id:
                flash("Страница уже существует", "info")
                return redirect(url_for("urls_url_id_get", url_id=url_id))

        new_url_id = repo.insert_url(base_url)
        logging.info(f"Inserted new URL {base_url} with ID: {new_url_id}.")
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("urls_url_id_get", url_id=new_url_id))


@app.route("/urls/<int:url_id>", methods=["GET"])
def urls_url_id_get(url_id):
    logging.info(f"Received GET request on /urls/{url_id} endpoint.")
    with DatabaseRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.get_url_data(url_id)
        checks = repo.get_url_checks(url_id)
    logging.info(f"Retrieved URL data for url_id {url_id}: {db_urls}")
    if not db_urls:
        logging.warning(f"URL for url_id {url_id} not found.")
        flash("URL not found.", "info")
        return redirect(url_for("main"))
    url_id, url_name, created_at = db_urls
    created_at = created_at.date()
    logging.info(
        f"Variables for url.html: url_id={url_id}, url_name={url_name}, created_at={created_at}, checks={checks}"
    )
    return render_template(
        "url.html",
        url_id=url_id,
        url_name=url_name,
        created_at=created_at,
        checks=checks,
    )


@app.route("/urls/<int:url_id>/checks", methods=["POST"])
def post_url_checks(url_id):
    logging.info(f"Received POST request on /urls/{url_id}/checks endpoint.")
    with DatabaseRepository(conn_str=DATABASE_URL) as repo:
        check_results = make_check(repo.get_url_name_by_id(url_id))
        if check_results["status_code"] != 500:
            repo.insert_url_check(url_id, check_results)
            logging.info("Url check success")
            flash("Страница успешно проверена", "info")
            return redirect(url_for("urls_url_id_get", url_id=url_id))
        logging.error(f'Url check failed. error: {check_results["error"]} ')
        flash("Произошла ошибка при проверке", "warning")
        return redirect(url_for("urls_url_id_get", url_id=url_id))


# @app.route("/logs", methods=["GET"])
# def get_logs():
#     try:
#         with open("app.log", "r") as log_file:
#             content = log_file.read()
#             return Response(content, content_type="text/plain; charset=utf-8")
#     except Exception as e:
#         return f"An error occurred: {e}", 500
