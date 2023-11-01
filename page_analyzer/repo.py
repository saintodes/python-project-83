import psycopg2


class DatabaseRepository:
    def __init__(self, conn_str):
        self.conn_str = conn_str
        self._initialize_connection_and_cursor()

    def __del__(self):
        self.close()

    # Connection Management

    def _initialize_connection_and_cursor(self):
        self.conn = psycopg2.connect(self.conn_str)
        self.cur = self.conn.cursor()

    def close(self):
        if hasattr(self, "cur") and self.cur:
            self.cur.close()
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

    # Internal Helper Methods

    def _execute_query(self, query, values=None):
        try:
            if values:
                self.cur.execute(query, values)
            else:
                self.cur.execute(query)
            self.conn.commit()
        except Exception as error:
            self.conn.rollback()
            raise error

    # URL Methods

    def fetch_url_id(self, url):
        query = "SELECT id FROM urls WHERE name = %s"
        self._execute_query(query, (url,))
        row = self.cur.fetchone()
        return row[0] if row else None

    def insert_url(self, url):
        query = "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id"
        self._execute_query(query, (url,))
        return self.cur.fetchone()[0]

    def get_url_data(self, url_id):
        query = "SELECT * FROM urls WHERE id = %s"
        self._execute_query(query, (url_id,))
        return self.cur.fetchone()

    def get_url_name_by_id(self, url_id):
        query = "SELECT name FROM urls WHERE id = %s"
        self._execute_query(query, (url_id,))
        return self.cur.fetchone()[0]

    # URL Checks Methods

    def insert_url_check(self, url_id, url_check_data):
        query = """
            INSERT INTO url_checks (url_id, created_at, status_code, h1, title, description)
            VALUES (%s, NOW(), %s, %s, %s, %s)
        """
        values = (
            url_id,
            url_check_data["status_code"],
            url_check_data["h1"],
            url_check_data["title"],
            url_check_data["description"],
        )
        self._execute_query(query, values)

    def get_url_checks(self, url_id):
        query = """
            SELECT id, url_id, status_code, h1, title, description, created_at
            FROM url_checks
            WHERE url_id = %s
            ORDER BY created_at DESC;
        """
        self._execute_query(query, (url_id,))
        return self.cur.fetchall()

    # Aggregate Data Methods

    def fetch_latest_url_data(self):
        query = """
        SELECT
        urls.id,
        urls.name,
        latest_checks.latest_check_at,
        url_checks.status_code
        FROM
            urls
        LEFT JOIN (
            SELECT
                url_id,
                MAX(created_at) AS latest_check_at
            FROM
                url_checks
            GROUP BY
                url_id
        ) AS latest_checks ON urls.id = latest_checks.url_id
        LEFT JOIN
            url_checks ON urls.id = url_checks.url_id AND latest_checks.latest_check_at = url_checks.created_at
        ORDER BY
            urls.id;
        """
        self._execute_query(query)
        return self.cur.fetchall()
