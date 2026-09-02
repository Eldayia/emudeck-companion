import tempfile
import unittest
from pathlib import Path

from companion_documents import DocumentIndex


class DocumentIndexTests(unittest.TestCase):
    def test_finds_esde_manual_and_game_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Emulation"
            rom_root = root / "roms"
            rom = rom_root / "psx" / "Final Fantasy VII.m3u"
            rom.parent.mkdir(parents=True)
            rom.touch()
            manual = root / "tools" / "downloaded_media" / "psx" / "manuals" / "FF7.pdf"
            manual.parent.mkdir(parents=True)
            manual.write_bytes(b"%PDF")
            document_root = root / "documents" / "psx" / "Final Fantasy VII"
            document_root.mkdir(parents=True)
            (document_root / "controls.md").write_text("Controls", encoding="utf-8")
            (document_root / "ignored.exe").touch()

            result = DocumentIndex(root, rom_root).lookup(str(rom), {"manual": str(manual)})

            self.assertEqual([item["title"] for item in result], ["Manual", "Controls"])
            self.assertTrue(result[0]["url"].startswith("file:"))
            self.assertEqual(result[1]["format"], "md")

    def test_ignores_missing_unsupported_and_duplicate_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / "Game.iso"
            rom.touch()
            manual = root / "Game.pdf"
            manual.write_bytes(b"%PDF")
            result = DocumentIndex(None, None).lookup(str(rom), {"manual": str(manual)})
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["title"], "Manual")
            other_rom = root / "Other.iso"
            other_rom.touch()
            (root / "Other.exe").touch()
            self.assertEqual(
                DocumentIndex(None, None).lookup(str(other_rom), {"manual": "missing.pdf"}),
                [],
            )


if __name__ == "__main__":
    unittest.main()
