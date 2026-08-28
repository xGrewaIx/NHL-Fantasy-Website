# Makefile for the NHL Fantasy Stats Website
# build automation commands for the project to build, run, test, lint, and format the code/application.

# This is the file where a portion of CI/CD pipeline is defined. It is used to automate the process of building, testing, and deploying the application.
# Make sure everytime code is added automatically run the check command to ensure that the code is linted and tested before committing it to the repository.
# Adding this in later on using github actions to automate the process of running the check command before merging code into the main branch.

# Need .PHONY to avoid conflicts with files named the following after the :
# this is because make checks if a file with the same name exists in the directory
# and if it does it will skip running the command 
.PHONY: install api web test lint format check

# create virtual environment and install dependencies
install:
	uv sync --extra dev

# run the API server using uvicorn (apps/api/main.py)
api:
	uv run uvicorn apps.api.main:app --reload

# run the Streamlit web application (apps/web/Home.py)
web:
	uv run streamlit run apps/web/Home.py

# run tests using pytest
test:
	uv run pytest

# run linting using ruff
lint:
	uv run ruff check .

# run code formatting using ruff
format:
	uv run ruff format .

# run linting and testing
# use before comitting code
check:
	uv run ruff check .
	uv run pytest