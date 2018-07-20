PYTHON_VERSION = 3.6.5
REQUIREMENTS_FILE = requirements.txt
REQUIREMENTS_DEV_FILE = requirements-dev.txt

env:
	pyenv local $(PYTHON_VERSION)
	python -m venv venv
	$(MAKE) install

install:
	python setup.py install

update: install

dev:
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

.PHONY: env test coverage lint dev clean install update
