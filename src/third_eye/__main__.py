"""Run the Phase 6 demonstration ASGI app.

Requires uvicorn::

    python -m third_eye
"""

from __future__ import annotations

import sys


def main() -> None:
    try:
        import uvicorn
    except ImportError:
        sys.stderr.write(
            "uvicorn is required to serve the Phase 6 API.\n"
            "Install it with: python -m pip install uvicorn\n"
            "Then run: python -m third_eye\n"
        )
        raise SystemExit(1) from None
    uvicorn.run(
        "third_eye.api.asgi:create_demo_app",
        factory=True,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
