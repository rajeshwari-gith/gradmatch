"""Find broken `website` links in the data files.

Every row in programs.csv and scholarships.csv points to an official page.
Run this on your own computer (it needs internet) after adding rows:

    PYTHONPATH=src python -m gradmatch.link_check            # checks data/
    PYTHONPATH=src python -m gradmatch.link_check some/dir   # checks another folder

It prints every link that does not open and exits with 1 if there are any.
It only reads the files; it never changes them. The test suite never calls
this against the real internet.
"""
import csv
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DATA_FILES = (
    ("programs.csv", "program_id"),
    ("scholarships.csv", "scholarship_id"),
)
USER_AGENT = "Mozilla/5.0 (GradMatch link checker; student project)"
TIMEOUT_SECONDS = 15
WORKERS = 8


def check_url(url: str, timeout: float = TIMEOUT_SECONDS) -> tuple[bool, str]:
    """Return (ok, detail). ok is True when the page opens (after redirects).

    Some sites refuse HEAD requests, so a failed HEAD is retried with GET.
    """
    if not url.startswith(("http://", "https://")):
        return False, "not an http(s) link"

    last = "no response"
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method,
                                         headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return True, str(response.status)
        except urllib.error.HTTPError as error:
            last = str(error.code)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            reason = getattr(error, "reason", error)
            last = f"error: {reason}"
    return False, last


def collect_links(data_dir) -> list[tuple[str, str, str]]:
    """Return (file name, row id, url) for every row that exists in data_dir."""
    links = []
    for file_name, id_column in DATA_FILES:
        path = Path(data_dir) / file_name
        if not path.exists():
            continue
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                links.append((file_name, row.get(id_column, "?"), (row.get("website") or "").strip()))
    return links


def find_broken(data_dir, checker=check_url) -> list[tuple[str, str, str, str]]:
    """Return (file, id, url, detail) for each link that does not open."""
    links = collect_links(data_dir)
    unique_urls = sorted({url for _, _, url in links})
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = dict(zip(unique_urls, pool.map(checker, unique_urls)))

    broken = []
    for file_name, row_id, url in links:
        ok, detail = results[url] if url else (False, "empty website")
        if not ok:
            broken.append((file_name, row_id, url, detail))
    return broken


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    data_dir = args[0] if args else Path(__file__).resolve().parents[2] / "data"

    links = collect_links(data_dir)
    if not links:
        print(f"No data rows found in {data_dir}.")
        return 1

    broken = find_broken(data_dir)
    print(f"Checked {len(links)} links in {data_dir}: {len(links) - len(broken)} open, {len(broken)} broken.")
    for file_name, row_id, url, detail in broken:
        print(f"  BROKEN  {file_name}  {row_id}  {url or '(empty)'}  [{detail}]")
    return 1 if broken else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
