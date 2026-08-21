import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pptx",
        action="store_true",
        default=False,
        help="run slow PPTX export tests",
    )
    parser.addoption(
        "--pptx-report",
        action="store",
        default=None,
        help="Specify Report to only create one report (default is all)",
    )
    parser.addoption(
        "--regen-golden",
        action="store_true",
        default=False,
        help="Regenerate golden benchmark test outputs.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--pptx"):
        return

    skip_pptx = pytest.mark.skip(reason="PPTX export is opt-in; pass --pptx to run")
    for item in items:
        if "pptx" in item.keywords:
            item.add_marker(skip_pptx)


@pytest.fixture
def regen_golden(request: pytest.FixtureRequest) -> bool:
    """Fixture that returns True if --regen-golden flag was passed."""
    return bool(request.config.getoption("--regen-golden"))
