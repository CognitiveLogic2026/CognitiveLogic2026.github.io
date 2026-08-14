import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("indexnow_submit", ROOT / "scripts/indexnow-submit.py")
indexnow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(indexnow)


class IndexNowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urls = indexnow.current_sitemap_urls(ROOT / "sitemap.xml", ROOT)

    def test_key_and_public_key_file(self):
        self.assertRegex(indexnow.KEY, re.compile(r"^[A-Za-z0-9-]{8,128}$"))
        self.assertEqual((ROOT / f"{indexnow.KEY}.txt").read_text(), indexnow.KEY + "\n")

    def test_ten_file_mappings(self):
        paths = [
            "index.html", "services.html", "framework.html", "academia/index.html",
            "resources/index.html", "resources/research-notes/index.html",
            "resources/documents/coste360-ea-001/index.html", "case-studies/index.html",
            "case-studies/coste360/index.html", "international-watch/index.html",
            "international-watch/frontier-ai-governance-demis-hassabis/index.html",
            "manifesto-verita-verificabile/index.html",
        ]
        mapped, fallback = indexnow.map_files(paths, ROOT, self.urls)
        self.assertFalse(fallback)
        self.assertEqual(len(mapped), len(paths))
        self.assertIn("https://cognitivelogic.it/", mapped)
        self.assertIn("https://cognitivelogic.it/manifesto-verita-verificabile/", mapped)

    def test_legacy_noindex_and_404_excluded(self):
        mapped, fallback = indexnow.map_files(
            ["case-studies.html", "privacy.html", "404.html"], ROOT, self.urls
        )
        self.assertFalse(fallback)
        self.assertEqual(mapped, [])
        self.assertNotIn("https://cognitivelogic.it/privacy.html", self.urls)

    def test_external_and_noncanonical_urls_rejected(self):
        for url in (
            "https://example.com/", "http://cognitivelogic.it/",
            "https://www.cognitivelogic.it/", "https://cognitivelogic.it/x?draft=1",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                indexnow.validate_url(url)

    def test_public_asset_uses_sitemap_fallback_signal(self):
        mapped, fallback = indexnow.map_files(["css/style.css"], ROOT, self.urls)
        self.assertEqual(mapped, [])
        self.assertTrue(fallback)

    def test_internal_and_runtime_changes_are_ignored(self):
        mapped, fallback = indexnow.map_files(
            ["tests/test_api.py", "main.py", "qen-sovereign/runtime.js", "source_retrieval.py"],
            ROOT, self.urls,
        )
        self.assertEqual(mapped, [])
        self.assertFalse(fallback)

    def test_hidden_and_unsafe_paths_are_ignored(self):
        mapped, fallback = indexnow.map_files(
            [".github/workflows/indexnow.yml", "../index.html", "/index.html"], ROOT, self.urls
        )
        self.assertEqual(mapped, [])
        self.assertFalse(fallback)

    def test_payload_is_valid_json_and_bounded(self):
        payload = indexnow.build_payload(self.urls[:2])
        decoded = json.loads(json.dumps(payload))
        self.assertEqual(decoded["keyLocation"], indexnow.KEY_LOCATION)
        self.assertLessEqual(len(decoded["urlList"]), indexnow.MAX_BATCH_SIZE)


if __name__ == "__main__":
    unittest.main()
