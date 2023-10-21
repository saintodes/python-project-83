from flask import (
    Flask,
    render_template,
    get_flashed_messages,
    flash,
    redirect,
    url_for,
    Response,
    request,
)
import psycopg2
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, Length, URL
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import logging


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


class UrlForm(FlaskForm):
    name = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=4, max=255),
            URL(allow_ip=True, message="Некорректный URL"),
        ],
    )


class MyRepository:
    def __init__(self, conn_str):
        self.conn_str = conn_str

    def __enter__(self):
        try:
            self.conn = psycopg2.connect(self.conn_str)
            self.cur = self.conn.cursor()
            return self
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cur.close()
        self.conn.close()

    def close(self):
        if hasattr(self, "cur") and self.cur:
            self.cur.close()
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

    def fetch_to_urls(self):
        query = """
            SELECT
            urls.id,
            urls.name,
            MAX(url_checks.created_at) AS latest_check_at
            FROM
                urls
            LEFT JOIN
                url_checks ON urls.id = url_checks.url_id
            GROUP BY
                urls.id, urls.name
            ORDER BY
                urls.id;
        """
        self.cur.execute(query)
        return self.cur.fetchall()

    def fetch_url_id(self, url):
        self.cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def url_exists(self, url):
        self.cur.execute("SELECT * FROM urls WHERE name = %s", (url,))
        return self.cur.fetchone() is not None

    def insert_url(self, url):
        self.cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id",
            (url,),
        )
        return self.cur.fetchone()[0]

    def get_urls_data_by_url_id(self, url_id):
        self.cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
        return self.cur.fetchone()

    def insert_url_check(self, url_id):
        self.cur.execute(
            "INSERT INTO url_checks (url_id, created_at) VALUES (%s, NOW())", (url_id,)
        )

    def get_url_checks(self, url_id):
        self.cur.execute(
            "SELECT id, created_at FROM url_checks WHERE url_id = %s ORDER BY created_at DESC",
            (url_id,),
        )
        return self.cur.fetchall()


@app.route("/", methods=["GET"])
def main():
    logging.info("Received GET request on main endpoint.")
    form = UrlForm()
    messages = get_flashed_messages(with_categories=True)
    if messages:
        logging.info(f"Flashed messages: {messages}")
    return render_template("main.html", messages=messages, form=form)


@app.route("/urls", methods=["GET"])
def urls_get():
    logging.info("Received GET request on /urls endpoint.")
    with MyRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.fetch_to_urls()
    logging.info(f"Retrieved {len(db_urls)} URL from the database.")
    logging.info(f"Variables for urls.html: db_urls={db_urls}")
    return render_template("urls.html", db_urls=db_urls)


@app.route("/urls", methods=["POST"])
def urls_post():
    logging.info("Received POST request on /urls endpoint.")
    form = UrlForm()
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

    with MyRepository(conn_str=DATABASE_URL) as repo:
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
    with MyRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.get_urls_data_by_url_id(url_id)
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
    print(f"url_id is {url_id}")
    logging.info(f"Received POST request on /urls/{url_id}/checks endpoint.")
    with MyRepository(conn_str=DATABASE_URL) as repo:
        repo.insert_url_check(url_id)
    flash("Страница успешно проверена", "success")
    return redirect(url_for("urls_url_id_get", url_id=url_id))


@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        with open("app.log", "r") as log_file:
            content = log_file.read()
            return Response(content, content_type="text/plain; charset=utf-8")
    except Exception as e:
        return f"An error occurred: {e}", 500
