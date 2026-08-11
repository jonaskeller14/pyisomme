import unittest
import io
import tarfile
import tempfile
import zipfile
from pathlib import Path

from pyisomme.sources import read_text_with_fallback, FolderSource, ZipSource, TarSource


class TestReadTextWithFallback(unittest.TestCase):
    def test_utf8(self):
        self.assertEqual(read_text_with_fallback("Prüfung".encode()), "Prüfung")

    def test_iso_8859_1_fallback(self):
        # 0xFC ("ü") is invalid UTF-8 but valid ISO-8859-1 -> must fall back, not raise.
        self.assertEqual(
            read_text_with_fallback("Prüfung".encode("iso-8859-1")), "Prüfung"
        )


class TestArchiveSources(unittest.TestCase):
    MEMBERS = {
        "11391/11391.mme": b"Test\n",
        "11391/Channel/11391.chn": b"Channel\n",
        "11391/Channel/11391.001": b"1.0\n2.0\n",
    }

    def _check(self, source):
        names = set(source.names())
        # Every data member must be listed and readable byte-for-byte.
        for name, content in self.MEMBERS.items():
            self.assertIn(name, names)
            self.assertEqual(source.read_bytes(name), content)
            self.assertEqual(source.read_text(name), content.decode("utf-8"))

    def test_folder_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, content in self.MEMBERS.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            self._check(FolderSource(root))

    def test_zip_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "container.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for name, content in self.MEMBERS.items():
                    zf.writestr(name, content)
            with ZipSource(zip_path) as source:
                self._check(source)

    def test_tar_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            tar_path = Path(tmp) / "container.tar"
            with tarfile.open(tar_path, "w") as tf:
                for name, content in self.MEMBERS.items():
                    info = tarfile.TarInfo(name)
                    info.size = len(content)
                    tf.addfile(info, io.BytesIO(content))
            with TarSource(tar_path) as source:
                self._check(source)


if __name__ == "__main__":
    unittest.main()
