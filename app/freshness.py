"""Notice when the gradmatch code on disk is newer than the copy loaded in memory.

Streamlit keeps imported modules in memory between runs and does not watch src/, so after an
update (for example a new deploy) the app script can be new while gradmatch is still the old
version, which shows up as an ImportError. The app calls forget_stale_gradmatch() before it
imports gradmatch; if the files changed, the old modules are dropped and re-imported fresh.
"""
from pathlib import Path


def source_signature(package_dir) -> tuple:
    """Same fingerprint as gradmatch.SOURCE_SIGNATURE, computed from the files on disk now."""
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size)
                 for p in sorted(Path(package_dir).glob("*.py")))


def forget_stale_gradmatch(package_dir, modules) -> bool:
    """Remove the loaded gradmatch modules from `modules` if the source files changed.

    Returns True if modules were removed. A package loaded before this check existed has no
    signature at all, which also counts as stale.
    """
    package = modules.get("gradmatch")
    if package is None:
        return False
    if getattr(package, "SOURCE_SIGNATURE", None) == source_signature(package_dir):
        return False
    for name in [n for n in modules if n == "gradmatch" or n.startswith("gradmatch.")]:
        del modules[name]
    return True
