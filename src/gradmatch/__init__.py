"""GradMatch: find graduate programs, funding, scholarships and deadlines."""
from pathlib import Path


def _source_signature():
    """A fingerprint of the package's source files (names, sizes and modification times).

    The Streamlit app compares it with the files on disk to notice that the code was updated
    while an old copy was still in memory (see app/freshness.py).
    """
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size)
                 for p in sorted(Path(__file__).parent.glob("*.py")))


# Computed once, when the package is first imported. app/freshness.py compares it with the disk.
SOURCE_SIGNATURE = _source_signature()
