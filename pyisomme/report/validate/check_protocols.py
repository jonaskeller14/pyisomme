from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pyisomme.report.validate.issue import Issue, IssueSeverity

if TYPE_CHECKING:
    from pyisomme.report.report import Report


def is_http_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except ValueError:
        return False


def check_protocols(report: Report) -> list[Issue]:
    issues: list[Issue] = []

    protocols = report.protocols
    if len(set(map(lambda r: r.version, protocols))) != len(protocols):
        issues.append(
            Issue(
                "protocols", IssueSeverity.ERROR, "", "Protocol versions are not unique"
            )
        )

    for protocol in protocols:
        for source in protocol.sources:
            # 1. HTTP/HTTPS URLs
            if is_http_url(source):
                continue

            # 2. Local File / Path checks
            if Path(source).exists():
                continue
            if Path(f"{source}.url").exists():
                continue

            issues.append(
                Issue(
                    "protocols",
                    IssueSeverity.WARNING,
                    "",
                    f"Source path does not exist: '{source}'",
                )
            )
    return issues
