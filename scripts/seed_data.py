"""Create the tutor state database directory."""

from __future__ import annotations

from app.storage.repository import Repository


def main() -> None:
    repo = Repository()
    print(f"Tutor database ready at {repo.path}")


if __name__ == "__main__":
    main()
