from flask import (
    Flask,
    render_template,
    get_flashed_messages,
    flash,
    redirect,
    url_for,
)
import psycopg2
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import InputRequired, Length, URL
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s"
)


load_dotenv()

app = Flask(__name__)
app.secret_key = "secret_key"

DATABASE_URL = os.getenv("DATABASE_URL")


class UrlForm(FlaskForm):
    name = StringField(
        "",
        validators=[
            InputRequired(),
            Length(min=4, max=255),
            URL(allow_ip=True, message="Invalid URL"),
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
    form = UrlForm()
    messages = get_flashed_messages(with_categories=True)
    if messages:
        logging.info(messages)
    return render_template("main.html", messages=messages, form=form)


@app.route("/urls", methods=["GET"])
def urls_get():
    with UrlRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.fetch_all_urls()
    logging.info(db_urls)
    return render_template("urls.html", db_urls=db_urls)


@app.route("/urls", methods=["POST"])
def urls_post():
    form = UrlForm()
    url = form.data.get("name")

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("main"))

    with UrlRepository(conn_str=DATABASE_URL) as repo:
        if repo.url_exists(url):
            url_id = repo.fetch_url_id(url)
            if url_id:
                flash("Страница уже существует", "info")
                return redirect(url_for("urls_slug_get", slug=url_id))
            else:
                flash("Такой сайт еще не проверялся.", "danger")
                return redirect(url_for("main"))

        new_url_id = repo.insert_url(url)
        flash("Страница успешно добавлена", "success")
        return redirect(url_for("urls_slug_get", slug=new_url_id))


@app.route("/urls/<int:slug>", methods=["GET"])
def urls_slug_get(slug):
    with UrlRepository(conn_str=DATABASE_URL) as repo:
        db_urls = repo.get_data(slug)
    logging.info(db_urls)

    if not db_urls:
        flash("URL not found.", "info")
        return redirect(url_for("main"))

    url_id, url_name, created_at = db_urls
    created_at = created_at.strftime("%Y-%m-%d")
    return render_template(
        "url.html", url_id=url_id, url_name=url_name, created_at=created_at
    )
