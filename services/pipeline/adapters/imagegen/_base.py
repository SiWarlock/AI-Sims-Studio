"""Shared helpers for the real async image adapters (imagegen 3.2; image3d 3.1 reuses these).

``safe_scratch_path`` derives a SAFE destination under the sidecar-provided scratch dir from a
provider-returned URL: strip to a basename (drop any path components), reject empty/dot names, and
verify the result stays under scratch (rule 3 / fp-4 — the mock's ``fetch`` guard is the analogue).
The §16 byte-cap / magic-byte hardening lands in 3.4.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit


def safe_scratch_path(scratch_dir: Path, url: str, *, index: int) -> Path:
    """A destination Path under ``scratch_dir`` for ``url``'s downloaded bytes, guaranteed not to
    escape scratch. Raises ValueError if the resolved path would escape (defense in depth).

    The ``index`` prefixes every filename so multiple outputs that share a basename
    (``.../a/concept.png`` and ``.../b/concept.png``) don't silently overwrite each other.
    """
    scratch_root = scratch_dir.resolve()
    # take the URL PATH only (drop query/fragment), then a bare filename — no "../" components
    name = Path(urlsplit(url).path.rsplit("/", 1)[-1]).name
    if name in ("", ".", ".."):
        name = "artifact.bin"
    dest = scratch_dir / f"{index:03d}-{name}"
    if not dest.resolve().is_relative_to(scratch_root):
        raise ValueError(f"fetch target escapes the scratch dir: {dest}")
    return dest
