"""Run the API examples written in README.md, so the README cannot drift from the code."""
# In plain words: the README shows `curl` commands for the API. If someone renames a parameter or
# an endpoint, those examples would quietly stop working, and a reader would copy a broken command.
# This test reads the README itself (the examples are not copied here), turns each curl command
# into the same request with FastAPI's TestClient, and checks the answer. So a change that breaks
# a README example fails the tests.
# The API runs on the small fixture data (tests/data_fixtures.py), like the other API tests.

import json
import re
import shlex
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from data_fixtures import write_fixture_data
from gradmatch.api import app

pytestmark = pytest.mark.integration

README = Path(__file__).resolve().parents[2] / "README.md"
SECTION_TITLE = "## Use the REST API"


def api_section() -> str:
    """The README text from the API heading up to the next "## " heading."""
    text = README.read_text(encoding="utf-8")
    start = text.index(SECTION_TITLE)
    end = text.find("\n## ", start + len(SECTION_TITLE))
    return text[start:] if end == -1 else text[start:end]


def curl_commands(section: str) -> list[str]:
    """Every curl command in the section's code blocks, with "\\" line continuations joined."""
    blocks = re.findall(r"```\n(.*?)```", section, re.S)
    joined = "\n".join(block.replace("\\\n", " ") for block in blocks)
    commands, current = [], None
    for line in joined.split("\n"):
        if line.startswith("curl "):
            current = line
            commands.append(current)
        elif current is not None and line.startswith(" "):
            commands[-1] += " " + line.strip()      # a body that goes on over several lines
        else:
            current = None
    return commands


def parse_curl(command: str) -> tuple[str, str, dict | None]:
    """curl [-X METHOD] "URL" [-H ...] [-d 'JSON']  ->  (method, path?query, body)."""
    words = shlex.split(command)
    method = words[words.index("-X") + 1] if "-X" in words else "GET"
    url = next(word for word in words if word.startswith("http"))
    body = json.loads(words[words.index("-d") + 1]) if "-d" in words else None
    parts = urlsplit(url)
    return method, parts.path + (f"?{parts.query}" if parts.query else ""), body


EXAMPLES = [parse_curl(command) for command in curl_commands(api_section())]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GRADMATCH_DATA_DIR", str(write_fixture_data(tmp_path)))
    return TestClient(app)


# ---- The README still has examples to check ----
# Why: if the section were renamed or the examples deleted, the tests below would check nothing
# and still pass. This makes that case fail instead.

def test_readme_has_the_api_examples():
    assert [(method, path.split("?")[0]) for method, path, _ in EXAMPLES] == [
        ("GET", "/programs"), ("POST", "/match"), ("GET", "/deadlines")]


# ---- Each example works ----
# Why: these are exactly the requests a reader will copy, so each must give 200 and the answer the
# README describes (a list for /programs and /deadlines; total_programs, programs and scholarships
# for /match), and must respect the limit it asks for.

@pytest.mark.parametrize("method, path, body", EXAMPLES, ids=[f"{m} {p}" for m, p, _ in EXAMPLES])
def test_readme_example_uses_only_real_parameters(method, path, body):
    # FastAPI quietly ignores a query parameter it does not know, so a renamed parameter would
    # still give 200. The API's own description (OpenAPI) lists the real parameter names.
    parts = urlsplit(path)
    operation = app.openapi()["paths"][parts.path][method.lower()]
    known = {parameter["name"] for parameter in operation.get("parameters", [])}

    assert set(parse_qs(parts.query)) <= known


@pytest.mark.parametrize("method, path, body", EXAMPLES, ids=[f"{m} {p}" for m, p, _ in EXAMPLES])
def test_readme_example_works(client, method, path, body):
    response = client.request(method, path, json=body)

    assert response.status_code == 200, response.text
    answer = response.json()
    limit = int(parse_qs(urlsplit(path).query).get("limit", ["1000"])[0])
    if path.startswith("/match"):
        assert set(answer) == {"total_programs", "programs", "scholarships"}
        assert len(answer["programs"]) <= limit
    else:
        assert isinstance(answer, list) and len(answer) <= limit


# ---- The other facts in the section ----
# Why: the table's /health answer and the uvicorn command are copied by readers too.

def test_health_answer_in_the_table_matches_the_api(client):
    row = next(line for line in api_section().split("\n") if line.startswith("| `GET /health`"))
    documented = json.loads(re.search(r"`(\{.*\})`", row).group(1))

    assert client.get("/health").json() == documented


def test_the_uvicorn_command_names_the_real_app():
    command = re.search(r"uvicorn (\S+):(\S+)", api_section())
    module, name = command.groups()

    assert (module, name) == ("gradmatch.api", "app")
    assert getattr(__import__(module, fromlist=[name]), name) is app


def test_uvicorn_is_installed_by_requirements():
    requirements = (README.parent / "requirements.txt").read_text().split()

    assert "uvicorn" in requirements
    assert "not in\n`requirements.txt`" not in api_section()     # the README must not say otherwise
