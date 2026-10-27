"""Integration tests for link_check.py.

A small web server runs on this computer, so the tests use real HTTP
requests but never touch the internet.

Techniques: equivalence partitioning on the kinds of answer a website can
give (200, 404, redirect, HEAD refused, server down, bad text).
"""
# In plain words: the link checker opens every website in the data to find dead links. Testing
# it on the real internet would be slow and would fail whenever a site is down, so these tests
# start a tiny fake web server on this computer that answers 200, 404, a redirect or "HEAD not
# allowed" on purpose. That way every kind of answer is tested, and the result is always the same.

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from gradmatch.link_check import check_url, collect_links, find_broken, main

pytestmark = pytest.mark.integration


# The fake website: each path gives one kind of answer, so each test can ask for the case it needs.
class Handler(BaseHTTPRequestHandler):
    def _reply(self, status, location=None):
        self.send_response(status)
        if location:
            self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _route(self):
        if self.path == "/ok":
            self._reply(200)
        elif self.path == "/moved":
            self._reply(302, "/ok")
        elif self.path == "/head-refused":
            self._reply(405 if self.command == "HEAD" else 200)
        else:
            self._reply(404)

    do_GET = do_HEAD = _route

    def log_message(self, *args):  # keep test output quiet
        pass


# Start the fake server once for this file on a free port, and stop it at the end.
@pytest.fixture(scope="module")
def site():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


# ---- check_url: one test per kind of answer ----
# Why (equivalence classes): one test per kind of answer a real website can give.

def test_working_page_is_ok(site):
    assert check_url(f"{site}/ok") == (True, "200")


def test_redirect_to_a_working_page_is_ok(site):
    assert check_url(f"{site}/moved")[0] is True


def test_missing_page_is_broken(site):
    assert check_url(f"{site}/nope") == (False, "404")


def test_site_that_refuses_head_is_retried_with_get(site):
    assert check_url(f"{site}/head-refused") == (True, "200")


def test_unreachable_server_is_broken():
    ok, detail = check_url("http://127.0.0.1:9/", timeout=2)
    assert not ok and detail.startswith("error:")


@pytest.mark.parametrize("text", ["", "not a link", "ftp://example.edu/page", "www.example.edu"])
def test_text_that_is_not_an_http_link_is_broken(text):
    assert check_url(text) == (False, "not an http(s) link")


# ---- collect_links and find_broken with temporary data files ----
# Why: the checker must find the links in both data files and report only the broken ones.

PROGRAM_HEADER = "program_id,website\n"
SCHOLARSHIP_HEADER = "scholarship_id,website\n"


def write_data(tmp_path, programs, scholarships):
    (tmp_path / "programs.csv").write_text(PROGRAM_HEADER + programs)
    (tmp_path / "scholarships.csv").write_text(SCHOLARSHIP_HEADER + scholarships)


def test_collect_links_reads_both_files(tmp_path):
    write_data(tmp_path, "P1,https://a.edu\nP2,https://b.edu\n", "S1,https://c.org\n")
    assert collect_links(tmp_path) == [
        ("programs.csv", "P1", "https://a.edu"),
        ("programs.csv", "P2", "https://b.edu"),
        ("scholarships.csv", "S1", "https://c.org"),
    ]


def test_collect_links_ignores_a_missing_file(tmp_path):
    (tmp_path / "programs.csv").write_text(PROGRAM_HEADER + "P1,https://a.edu\n")
    assert collect_links(tmp_path) == [("programs.csv", "P1", "https://a.edu")]


def test_find_broken_reports_only_the_bad_rows(site, tmp_path):
    write_data(tmp_path, f"P1,{site}/ok\nP2,{site}/nope\nP3,\n", f"S1,{site}/moved\nS2,{site}/gone\n")
    broken = find_broken(tmp_path)
    assert [(f, i, d) for f, i, _, d in broken] == [
        ("programs.csv", "P2", "404"),
        ("programs.csv", "P3", "empty website"),
        ("scholarships.csv", "S2", "404"),
    ]


def test_same_link_used_twice_is_checked_once(tmp_path):
    calls = []

    def fake_checker(url):
        calls.append(url)
        return True, "200"

    write_data(tmp_path, "P1,https://a.edu\nP2,https://a.edu\n", "S1,https://a.edu\n")
    assert find_broken(tmp_path, checker=fake_checker) == []
    assert calls == ["https://a.edu"]


# ---- main: exit code and printed summary ----
# Why: exit code 1 lets a script or CI notice broken links; the summary tells a person which ones.

def test_main_returns_0_when_every_link_opens(site, tmp_path, capsys):
    write_data(tmp_path, f"P1,{site}/ok\n", f"S1,{site}/ok\n")
    assert main([str(tmp_path)]) == 0
    assert "Checked 2 links" in capsys.readouterr().out


def test_main_returns_1_and_lists_broken_links(site, tmp_path, capsys):
    write_data(tmp_path, f"P1,{site}/ok\nP2,{site}/nope\n", f"S1,{site}/ok\n")
    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "1 broken" in output
    assert f"BROKEN  programs.csv  P2  {site}/nope  [404]" in output


def test_main_returns_1_when_there_is_no_data(tmp_path, capsys):
    assert main([str(tmp_path)]) == 1
    assert "No data rows found" in capsys.readouterr().out


def test_main_without_an_argument_checks_the_data_folder(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr("gradmatch.link_check.collect_links",
                        lambda data_dir: seen.append(str(data_dir)) or [])
    assert main([]) == 1
    assert seen[0].endswith("data")
    assert "No data rows found" in capsys.readouterr().out
