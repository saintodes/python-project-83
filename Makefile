install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

debug:
	poetry run flask --app page_analyzer:app --debug run 

lint:
	poetry run flake8 page_analyzer/ --count --select=E9,F63,F7,F82 --show-source --statistics
# stop the build if there are Python syntax errors or undefined names
	poetry run flake8 page_analyzer/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
# stop the build if there are Python syntax errors or undefined names

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app