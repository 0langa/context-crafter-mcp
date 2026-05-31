from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    server_path = repo / "src" / "context_crafter_mcp" / "server.py"
    text = server_path.read_text(encoding="utf-8")
    noisy_markers = ["print(", "logging.basicConfig", "logger.info(", "logger.warning("]
    bad = [marker for marker in noisy_markers if marker in text]
    if bad:
        sys.stderr.write("Hook fail: potential stdio noise markers in server.py -> " + ", ".join(bad) + "\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
