from psycopg2 import pool


class DatabaseRepository:
    def __init__(self, conn_str):
        self.conn_str = conn_str
        self.connection_pool = pool.SimpleConnectionPool(minconn=1, maxconn=1, dsn=self.conn_str)

    # Connection Management
    def _get_connection(self):
        return self.connection_pool.getconn()

    def _release_connection(self, conn):
        self.connection_pool.putconn(conn)

    def _execute_query(self, query, values=None):
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()
                # Fetchall if we've got any
                if cur.description:
                    return cur.fetchall()
        except Exception as error:
            conn.rollback()
            raise error
        finally:
            self._release_connection(conn)

    def close_connection_pool(self):
        self.connection_pool.closeall()

    # URL Methods

    def get_url_id_by_name(self, url):
        query = "SELECT id FROM urls WHERE name = %s"
        rows = self._execute_query(query, (url,))
        return rows[0][0] if rows else None

    def insert_url_and_return_id(self, url):
        query = "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id"
        rows = self._execute_query(query, (url,))
        return rows[0][0] if rows else None

    def get_url_data(self, url_id):
        query = "SELECT * FROM urls WHERE id = %s"
        rows = self._execute_query(query, (url_id,))
        return rows[0] if rows else None

    def get_url_name_by_id(self, url_id):
        query = "SELECT name FROM urls WHERE id = %s"
        rows = self._execute_query(query, (url_id,))
        return rows[0][0] if rows else None

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
        return self._execute_query(query, (url_id,))

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
        return self._execute_query(query)
