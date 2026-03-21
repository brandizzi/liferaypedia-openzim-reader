import unittest

from liferaypedia_openzim_reader.htmlinspector import (
    HtmlInspector,
    href_to_category_zim_path,
)


class GetMainContentTests(unittest.TestCase):
    def test_extracts_content_from_main_element(self) -> None:
        html = """
        <html>
            <body>
                <ul><li>A</li></ul>
                <main><h1>Title</h1><p>Text</p></main>
            </body>
        </html>
        """
        self.assertEqual(
            HtmlInspector(html).get_main_content(),
            "<h1>Title</h1><p>Text</p>",
        )

    def test_trims_content(self) -> None:
        html = """
        <html>
            <body>
                <ul><li>A</li></ul>
                <main>\t\t\n\r\n
                <h1>Title</h1><p>Text</p>\t\n\r\n</main>
            </body>
        </html>
        """
        self.assertEqual(
            HtmlInspector(html).get_main_content(),
            "<h1>Title</h1><p>Text</p>",
        )


class IsRedirectByMetaTagTests(unittest.TestCase):
    def test_meta_refresh_is_redirect(self) -> None:
        html = """
        <!DOCTYPE html>
        <html>
          <head>
            <meta http-equiv="refresh" content="5">
          </head>
        </html>
        """
        self.assertTrue(HtmlInspector(html).is_redirect_by_meta_tag())

    def test_meta_refresh_is_case_insensitive(self) -> None:
        html = """
        <html>
          <head>
            <meta HTTP-EQUIV="REFRESH" content="5">
          </head>
        </html>
        """
        self.assertTrue(HtmlInspector(html).is_redirect_by_meta_tag())

    def test_no_meta_or_no_content_is_not_redirect(self) -> None:
        html_without_meta = """
        <html><head><title>Test</title></head></html>
        """
        malformed_html = """
        html><head<><meta charset="UTF-8"><title>Test</title></head></html>
        """
        meta_without_content = """
        <html><head><meta http-equiv="refresh"></head></html>
        """

        self.assertFalse(HtmlInspector(html_without_meta).is_redirect_by_meta_tag())
        self.assertFalse(HtmlInspector(malformed_html).is_redirect_by_meta_tag())
        self.assertFalse(
            HtmlInspector(meta_without_content).is_redirect_by_meta_tag()
        )
        self.assertFalse(HtmlInspector("").is_redirect_by_meta_tag())


class HrefToCategoryZimPathTests(unittest.TestCase):
    """Behaviour of ``href_to_category_zim_path`` (ZIM-style ``Category/...`` output)."""

    def test_zim_style_slash_prefix_stripped(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("/Category/Sample_Cat"),
            "Category/Sample_Cat",
        )

    def test_mediawiki_colon_relative(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("./Category:Sample_Cat"),
            "Category/Sample_Cat",
        )

    def test_spaces_normalized_to_underscores(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("Category:Foo Bar"),
            "Category/Foo_Bar",
        )

    def test_subpath_after_category_slash_preserved(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("Category/Foo/Bar"),
            "Category/Foo/Bar",
        )

    def test_en_wikipedia_wiki_url_strips_query(self) -> None:
        self.assertEqual(
            href_to_category_zim_path(
                "https://en.wikipedia.org/wiki/Category:Foo?q=1"
            ),
            "Category/Foo",
        )

    def test_commons_wiki_url(self) -> None:
        self.assertEqual(
            href_to_category_zim_path(
                "https://commons.wikimedia.org/wiki/Category:Amphibia"
            ),
            "Category/Amphibia",
        )

    def test_protocol_relative_wiki_url(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("//en.wikipedia.org/wiki/Category:Z"),
            "Category/Z",
        )

    def test_index_php_title_query(self) -> None:
        self.assertEqual(
            href_to_category_zim_path(
                "https://en.wikipedia.org/w/index.php?title=Category%3ATest_Cat"
            ),
            "Category/Test_Cat",
        )

    def test_zim_main_namespace_prefix(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("-/Category:Living_people"),
            "Category/Living_people",
        )

    def test_wiki_prefix_segment(self) -> None:
        self.assertEqual(
            href_to_category_zim_path("/wiki/Category:Side_path"),
            "Category/Side_path",
        )

    def test_non_category_wiki_article_returns_none(self) -> None:
        self.assertIsNone(
            href_to_category_zim_path("https://en.wikipedia.org/wiki/Foo?q=1")
        )

    def test_empty_and_non_link_hrefs_return_none(self) -> None:
        self.assertIsNone(href_to_category_zim_path(""))
        self.assertIsNone(href_to_category_zim_path("   "))
        self.assertIsNone(href_to_category_zim_path("#section"))
        self.assertIsNone(href_to_category_zim_path("javascript:void(0)"))
        self.assertIsNone(href_to_category_zim_path("mailto:a@b"))


class ExtractCategoryAndImagePathsTests(unittest.TestCase):
    """``HtmlInspector.extract_category_and_image_paths`` scans the full document."""

    def test_zim_category_href_plus_image(self) -> None:
        html = '<p><a href="/Category/Sample_Cat">Cat</a><img src="/I/pic.png"/></p>'
        cats, imgs = HtmlInspector(html).extract_category_and_image_paths()
        self.assertEqual(cats, ["Category/Sample_Cat"])
        self.assertEqual(imgs, ["I/pic.png"])

    def test_category_colon_in_footer(self) -> None:
        html = '<footer><a href="./Category:Sample_Cat">c</a></footer>'
        cats, imgs = HtmlInspector(html).extract_category_and_image_paths()
        self.assertEqual(cats, ["Category/Sample_Cat"])
        self.assertEqual(imgs, [])

    def test_absolute_wiki_category_url(self) -> None:
        html = (
            '<a href="https://en.wikipedia.org/wiki/Category:Foo_Bar">x</a>'
        )
        cats, imgs = HtmlInspector(html).extract_category_and_image_paths()
        self.assertEqual(cats, ["Category/Foo_Bar"])
        self.assertEqual(imgs, [])

    def test_category_outside_main_is_included(self) -> None:
        html = (
            "<main><p>x</p></main>"
            '<footer><a href="Category:Footer_Cat">c</a></footer>'
        )
        cats, imgs = HtmlInspector(html).extract_category_and_image_paths()
        self.assertEqual(cats, ["Category/Footer_Cat"])
        self.assertEqual(imgs, [])

    def test_deduplicates_same_category(self) -> None:
        html = (
            '<a href="Category:A">1</a>'
            '<a href="./Category:A">2</a>'
            '<a href="https://en.wikipedia.org/wiki/Category:A">3</a>'
        )
        cats, _ = HtmlInspector(html).extract_category_and_image_paths()
        self.assertEqual(cats, ["Category/A"])

    def test_non_category_anchors_ignored(self) -> None:
        html = '<a href="Alcoholism">a</a><a href="#cite">b</a>'
        cats, imgs = HtmlInspector(html).extract_category_and_image_paths()
        self.assertEqual(cats, [])
        self.assertEqual(imgs, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
