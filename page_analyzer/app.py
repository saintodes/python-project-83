from flask import (
    Flask,
    render_template,
    get_flashed_messages,
    flash,
    redirect,
    url_for,
    Response
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


class UrlRepository:
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

    def fetch_all_urls(self, offset=0, limit=10):
        self.cur.execute("SELECT * FROM urls ORDER BY id DESC;")
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

    def get_data(self, slug):
        self.cur.execute("SELECT * FROM urls WHERE id = %s", (slug,))
        return self.cur.fetchone()


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
    with UrlRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.fetch_all_urls()
    logging.info(f"Retrieved {len(db_urls)} URL from the database.")
    return render_template("urls.html", db_urls=db_urls)


@app.route("/urls", methods=["POST"])
def urls_post():
    logging.info("Received POST request on /urls endpoint.")
    form = UrlForm()
    full_url = form.data.get("name")
    
    parsed_url = urlparse(full_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    if not form.validate_on_submit():
        logging.warning(f"Form validation failed for URL: {base_url}. Errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("main"))

    with UrlRepository(conn_str=DATABASE_URL) as repo:
        if repo.url_exists(base_url):
            logging.info(f"URL {base_url} already exists in the database.")
            url_id = repo.fetch_url_id(base_url)
            if url_id:
                flash("Страница уже существует", "info")
                return redirect(url_for("urls_slug_get", slug=url_id))

        new_url_id = repo.insert_url(base_url)
        logging.info(f"Inserted new URL {base_url} with ID: {new_url_id}.")
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("urls_slug_get", slug=new_url_id))



@app.route("/urls/<int:slug>", methods=["GET"])
def urls_slug_get(slug):
    logging.info(f"Received GET request on /urls/{slug} endpoint.")
    with UrlRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.get_data(slug)
    logging.info(f"Retrieved URL data for slug {slug}: {db_urls}")

    if not db_urls:
        logging.warning(f"URL for slug {slug} not found.")
        flash("URL not found.", "info")
        return redirect(url_for("main"))

    url_id, url_name, created_at = db_urls
    created_at = created_at.strftime("%Y-%m-%d")
    return render_template(
        "url.html", url_id=url_id, url_name=url_name, created_at=created_at
    )

@app.route("/logs", methods=['GET'])
def get_logs():
    try:
        with open("app.log", "r") as log_file:
            content = log_file.read()
            return Response(content, content_type="text/plain; charset=utf-8")
    except Exception as e:
        return f"An error occurred: {e}", 500