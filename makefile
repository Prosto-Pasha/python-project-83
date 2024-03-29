build:
	poetry build

install:
	poetry install

package-install:
	python3 -m pip install --user dist/*.whl

package-reinstall:
	python3 -m pip install --force-reinstall --user dist/*.whl

selfcheck:
	poetry check

test-coverage:
	poetry run pytest --cov=page_analyzer --cov-report xml -vv

lint:
	poetry run flake8 page_analyzer

check: selfcheck lint

schema-load:
	psql database < database.sql

dev:
	poetry run flask --app page_analyzer:app --debug run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
