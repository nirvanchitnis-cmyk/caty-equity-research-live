"""Module entrypoint for `python -m tools.ir_materials_extract`."""

from .cli import main


def run() -> None:
    """Invoke the CLI entrypoint."""
    main()


if __name__ == "__main__":  # pragma: no cover
    run()
