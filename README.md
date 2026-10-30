# GradMatch

**Course:** SE 413/513 – Software Testing
**Track:** B – Testing a Newly-Developed System
**Team Members:** Rajeshwari Galugu and Sai Nishith Jangili

## Project Description

GradMatch is a simple Python application that helps students plan for graduate school. Students
enter their degree, field, GPA, home state and yearly budget. The app shows the programs they can
afford with their chance of getting in, the scholarships they can apply for, and upcoming
deadlines. The data (159 programs and 7 scholarships) is stored in a SQLite database.

Live app: https://gradmatch-rg.streamlit.app

## Technologies Used

Python, Streamlit, SQLite, pytest, and pytest-cov.

## Installation

Install the required dependencies:

`python -m pip install -r requirements.txt`

## Run the Application

`python -m streamlit run app.py`

## Run Automated Tests

`python -m pytest -v`

## Generate Coverage Report

`python -m pytest --cov=app --cov=programs --cov=scholarships --cov=database --cov-branch --cov-report=term-missing`

## Current Testing Results

15 automated tests pass, with 100% line and branch coverage. The test plan and defect log are in
`TEST_PLAN.md`.

## Project Status

The application and the unit, integration, system and acceptance tests are complete. The final
report and presentation are planned for later project milestones.
