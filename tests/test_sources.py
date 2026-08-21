import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from pyisomme.sources import FolderSource, TarSource, ZipSource, read_text_with_fallback

# Itemized test data
SAMPLE_MEMBERS = {
    "11391/11391.mme": b"Test\n",
    "11391/Channel/11391.chn": b"Channel\n",
    "11391/Channel/11391.001": b"1.0\n2.0\n",
}


@pytest.mark.parametrize(
    "encoded_bytes, expected",
    [
        ("Prüfung".encode(), "Prüfung"),
        # 0xFC ("ü") is invalid UTF-8 but valid ISO-8859-1 -> must fall back, not raise.
        ("Prüfung".encode("iso-8859-1"), "Prüfung"),
    ],
)
def test_read_text_with_fallback(encoded_bytes: bytes, expected: str) -> None:
    assert read_text_with_fallback(encoded_bytes) == expected


class TestArchiveSources:
    @pytest.fixture
    def folder_source(self, tmp_path: Path) -> FolderSource:
        for name, content in SAMPLE_MEMBERS.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return FolderSource(tmp_path)

    @pytest.fixture
    def zip_source(self, tmp_path: Path):
        zip_path = tmp_path / "container.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in SAMPLE_MEMBERS.items():
                zf.writestr(name, content)
        with ZipSource(zip_path) as source:
            yield source

    @pytest.fixture
    def tar_source(self, tmp_path: Path):
        tar_path = tmp_path / "container.tar"
        with tarfile.open(tar_path, "w") as tf:
            for name, content in SAMPLE_MEMBERS.items():
                info = tarfile.TarInfo(name)
                info.size = len(content)
                tf.addfile(info, io.BytesIO(content))
        with TarSource(tar_path) as source:
            yield source

    @pytest.mark.parametrize(
        "source_fixture", ["folder_source", "zip_source", "tar_source"]
    )
    def test_archive_contents(
        self, request: pytest.FixtureRequest, source_fixture: str
    ) -> None:
        source = request.getfixturevalue(source_fixture)
        names = set(source.names())

        for name, content in SAMPLE_MEMBERS.items():
            assert name in names
            assert source.read_bytes(name) == content
            assert source.read_text(name) == content.decode("utf-8")
