VENV_PATH = venv
VENV_BIN = $(VENV_PATH)/bin
PY_PKG_ROOT=transformer
PYTHON_VERSION = 3.6.5
REQUIREMENTS_FILE = requirements.txt
REQUIREMENTS_DEV_FILE = requirements-dev.txt
NOSE_FLAGS = -s --with-coverage --cover-inclusive --cover-erase --cover-package=$(PY_PKG_ROOT)
MYPY_FLAGS = --ignore-missing-imports

env:
	pyenv local $(PYTHON_VERSION)
	test -d $(VENV_PATH) || python -m venv $(VENV_PATH)

install:
	$(VENV_BIN)/pip install .

install-dev:
	$(VENV_BIN)/pip install -e .[dev]

update: install

lint:
	$(VENV_BIN)/flake8 $(PY_PKG_ROOT) tests
	$(VENV_BIN)/mypy $(PY_PKG_ROOT) $(MYPY_FLAGS)

test:
	$(VENV_BIN)/nosetests $(NOSE_FLAGS)

test-loop:
	watch -n 5 "make lint && make test"

run:
	gunicorn --paste etc/local.ini --reload

clean:
	pipenv --rm
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build

.PHONY: env install-dev lint test clean
