install:
	poetry install

gr:
	chmod +x ./build.sh && chmod +x ./dev-build.sh && chmod +x ./dev-build-render-db.sh

build:
	./build.sh

dev-build:
	./dev-build.sh

dev-build-render-db:
	./dev-build-render-db.sh

start-dev-local:
	poetry run flask --app page_analyzer:app run --debug --port 5000 --host 127.0.0.1 

start-dev-external:
	poetry run flask --app page_analyzer:app run --debug --port 5000 --host 0.0.0.0

lint:
	poetry run flake8 page_analyzer/ --count --select=E9,F63,F7,F82 --show-source --statistics
# stop the build if there are Python syntax errors or undefined names
	poetry run flake8 page_analyzer/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
# stop the build if there are Python syntax errors or undefined names

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

drop-table:
	udo -u postgres psql -c "DROP DATABASE IF EXISTS dev_database;"

drop-role:
	sudo -u postgres psql -c "DROP ROLE IF EXISTS dev_db_user;"

start-local:
	poetry run gunicorn -w 5 -b 127.0.0.1:8000 page_analyzer:app