import unittest
from pathlib import Path

from liferaypedia_openzim_reader.zimreader import (
    deduce_namespace,
    get_entry_type_and_namespace,
    iter_zim_entries,
    to_skip,
)
import liferaypedia_openzim_reader.zimreader as zimreader


class IterZimEntriesTests(unittest.TestCase):
    def test_iter_zim_entries_matches_expected_sample(self) -> None:
        pkg_dir = Path(zimreader.__file__).resolve().parent
        test_zim = pkg_dir / "tests" / "resources" / "test.zim"

        entries = list(iter_zim_entries(str(test_zim), max_objects=4))

        self.assertEqual(
            entries[0],
            {
                "id": 1,
                "path": "A/Sample_Article",
                "title": "Sample Article",
                "type": "article",
                "mime_type": "text/html",
                "is_redirect": False,
                "namespace": "A",
                "content": "<h1>Sample Article</h1>\n<p>This article contains an image and a category link.</p>\n<figure>\n<img alt=\"Sample image\" src=\"/I/sample.png\"/>\n<figcaption>Sample image</figcaption>\n</figure>\n<p>Category: <a href=\"/Category/Sample_Category\">Sample Category</a></p>",
                "size_bytes": 399,
                "category_paths": ["Category/Sample_Category"],
                "image_paths": ["I/sample.png"],
            },
        )

        self.assertEqual(
            entries[1],
            {
                "id": 2,
                "path": "Category/Sample_Category",
                "title": "Sample Category",
                "type": "category",
                "mime_type": "text/html",
                "is_redirect": False,
                "namespace": "Category",
                "content": "<h1>Category: Sample Category</h1>\n<ul>\n<li><a href=\"/A/Sample_Article\">Sample Article</a></li>\n</ul>",
                "size_bytes": 240,
            },
        )

        self.assertEqual(
            entries[2],
            {
                "id": 3,
                "path": "I/sample.png",
                "title": "sample.png",
                "type": "image",
                "mime_type": "image/png",
                "is_redirect": False,
                "namespace": "I",
                "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
                "size_bytes": 70,
            },
        )

        self.assertEqual(
            entries[3],
            {
                "id": 4,
                "path": "Counter",
                "title": "Counter",
                "type": "page",
                "mime_type": "text/plain",
                "is_redirect": False,
                "namespace": "main",
                "content": "image/png=1;text/html=2",
                "size_bytes": 23,
            },
        )


class DeduceNamespaceTests(unittest.TestCase):
    def test_examples_from_docstring(self) -> None:
        self.assertEqual(deduce_namespace("I/cat.png"), "I")
        self.assertEqual(deduce_namespace("-/Main_Page"), "main")
        self.assertEqual(deduce_namespace("/Entry"), "main")
        self.assertEqual(deduce_namespace("lostmedia"), "main")


class GetEntryTypeAndNamespaceTests(unittest.TestCase):
    def test_examples_from_docstring(self) -> None:
        self.assertEqual(get_entry_type_and_namespace("-/Main_Page"), ("page", "main"))
        self.assertEqual(get_entry_type_and_namespace("A/Bobsled"), ("article", "A"))
        self.assertEqual(
            get_entry_type_and_namespace("humanities.jpg"), ("page", "main")
        )
        self.assertEqual(get_entry_type_and_namespace("I/cat.png"), ("image", "I"))
        self.assertEqual(get_entry_type_and_namespace("I/cat.mp4"), ("image", "I"))

        self.assertEqual(
            get_entry_type_and_namespace("File/cat.png"), ("image", "File")
        )
        self.assertEqual(
            get_entry_type_and_namespace("File/novel.pdf"), ("document", "File")
        )
        self.assertEqual(
            get_entry_type_and_namespace("File/jazz.ogg"), ("audio", "File")
        )


class ToSkipTests(unittest.TestCase):
    def test_examples_from_docstring(self) -> None:
        class TestItem:
            def __init__(self, mimetype: str = "text/html"):
                self.mimetype = mimetype

        class TestEntry:
            def __init__(self, is_redirect: bool = False, mime_type: str = "text/html"):
                self.is_redirect = is_redirect
                self.item = TestItem(mime_type)

            def get_item(self):
                return self.item

        self.assertTrue(to_skip(TestEntry(mime_type="application/javascript")))
        self.assertTrue(to_skip(TestEntry(is_redirect=True, mime_type="text/html")))
        self.assertFalse(to_skip(TestEntry(is_redirect=False, mime_type="text/html")))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

