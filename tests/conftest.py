import matplotlib
import pytest

# Keep plotting tests independent of a locally configured interactive backend.
# This must run before test modules import ``matplotlib.pyplot``.
matplotlib.use("Agg")


def pytest_configure(config: pytest.Config) -> None:
    for marker, description in (
        ("pptx", "PPTX report export tests"),
        ("html", "HTML report export tests"),
        ("pdf", "PDF report export tests"),
    ):
        config.addinivalue_line("markers", f"{marker}: {description}")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pptx",
        action="store_true",
        default=False,
        help="run slow PPTX export tests",
    )
    parser.addoption(
        "--report",
        action="store",
        default=None,
        help="Specify Report to only create one report (default is all)",
    )
    parser.addoption(
        "--html",
        action="store_true",
        default=False,
        help="run slow HTML export tests",
    )
    parser.addoption(
        "--pdf",
        action="store_true",
        default=False,
        help="run slow PDF export tests",
    )
    parser.addoption(
        "--regen-golden",
        action="store_true",
        default=False,
        help="Regenerate golden benchmark test outputs.",
    )


def pytest_collection_modifyitems(config, items):
    export_options = {
        "pptx": ("--pptx", "PPTX"),
        "html": ("--html", "HTML"),
        "pdf": ("--pdf", "PDF"),
    }
    for item in items:
        for marker, (option, label) in export_options.items():
            if marker in item.keywords and not config.getoption(option):
                item.add_marker(
                    pytest.mark.skip(
                        reason=f"{label} export is opt-in; pass {option} to run"
                    )
                )


@pytest.fixture
def regen_golden(request: pytest.FixtureRequest) -> bool:
    """Fixture that returns True if --regen-golden flag was passed."""
    return bool(request.config.getoption("--regen-golden"))
