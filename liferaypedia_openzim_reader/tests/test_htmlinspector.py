import unittest

from liferaypedia_openzim_reader.htmlinspector import (
    get_main_content,
    is_redirect_by_meta_tag,
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
        self.assertEqual(get_main_content(html), "<h1>Title</h1><p>Text</p>")

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
        self.assertEqual(get_main_content(html), "<h1>Title</h1><p>Text</p>")

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
        self.assertTrue(is_redirect_by_meta_tag(html))

    def test_meta_refresh_is_case_insensitive(self) -> None:
        html = """
        <html>
          <head>
            <meta HTTP-EQUIV="REFRESH" content="5">
          </head>
        </html>
        """
        self.assertTrue(is_redirect_by_meta_tag(html))

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

        self.assertFalse(is_redirect_by_meta_tag(html_without_meta))
        self.assertFalse(is_redirect_by_meta_tag(malformed_html))
        self.assertFalse(is_redirect_by_meta_tag(meta_without_content))
        self.assertFalse(is_redirect_by_meta_tag(""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

