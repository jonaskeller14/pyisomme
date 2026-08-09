import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the unit test suite across Python versions."""
    session.install(".")
    if session.posargs:
        session.run("python", "-m", "unittest", *session.posargs)
    else:
        session.run("python", "-m", "unittest", "discover", "-s", "tests")


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run ruff linter and formatter checks."""
    session.install("ruff")
    # Allows passing specific files or flags (e.g., nox -s lint -- --fix or nox -s lint -- pyisomme/channel.py)
    targets = session.posargs if session.posargs else ["."]
    session.run("ruff", "check", *targets)
    session.run("ruff", "format", "--check", *targets)


@nox.session(python="3.12")
def type_check(session: nox.Session) -> None:
    """Run mypy type checker."""
    session.install(".", "mypy")
    # Allows overriding target directory or passing flags like --strict
    targets = session.posargs if session.posargs else ["pyisomme"]
    session.run("mypy", *targets)
