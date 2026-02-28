# liferaypedia_openzim_reader/html_parser.py
"""
HTML parsing functions for the LiferayPedia OpenZIM Reader package.

This module provides the HtmlInspector class for parsing HTML content,
extracting main content, and detecting redirect meta tags.
"""

from bs4 import BeautifulSoup


class HtmlInspector:
    """
    Inspect HTML content. content may be str or a BeautifulSoup instance (or Tag).
    """

    def __init__(self, content):
        assert isinstance(content, str)
        self.content = content
        self.soup = BeautifulSoup(content, "html.parser")

    def get_main_content(self):
        """
        Return the content from the <main> element::

        >>> HtmlInspector('''
        ... <html>
        ...     <body>
        ...         <ul><li>A</li></ul>
        ...         <main>
        ...             <h1>Title</h1><p>Text</p>
        ...         </main>
        ...     </body>
        ... </html>
        ... ''').get_main_content()
        '<h1>Title</h1><p>Text</p>'
        """
        main = self.soup.find("main")
        return main.decode_contents().strip() if main else ""

    def is_redirect_by_meta_tag(self):
        """
        Check if the document contains a meta tag that causes page to refresh::

        >>> HtmlInspector('''
        ... <!DOCTYPE html><html><head><meta http-equiv="refresh" content="5"></head></html>
        ... ''').is_redirect_by_meta_tag()
        True

        It should be case-insensitive::

        >>> HtmlInspector('''
        ... <html>head><meta HTTP-EQUIV="REFRESH" content="5"></head></html>
        ... ''').is_redirect_by_meta_tag()
        True

        Of course, it should return false if there is no meta tag, or if there are
        meta tags that do not refresh, or if there is no content on it::

        >>> HtmlInspector('''
        ... <html><head><title>Test</title></head></html>
        ... ''').is_redirect_by_meta_tag()
        False
        >>> HtmlInspector('''
        ... html><head<><meta charset="UTF-8"><title>Test</title></head></html>
        ... ''').is_redirect_by_meta_tag()
        False
        >>> HtmlInspector('''
        ... <html><head><meta http-equiv="refresh"></head></html>
        ... ''').is_redirect_by_meta_tag()
        False
        >>> HtmlInspector('').is_redirect_by_meta_tag()
        False
        """
        for meta in self.soup.find_all("meta"):
            http_equiv = meta.get("http-equiv", "").lower()
            if http_equiv == "refresh":
                meta_content = meta.get("content", "")
                if meta_content:
                    return True
        return False

    def extract_category_and_image_paths(self):
        """
        Extract category and image paths from HTML content.

        Returns (category_paths, image_paths) where each path is in ZIM format
        (e.g. "Category/Name", "I/filename.png"). If root is given, search within
        that element; otherwise search the whole document::

        >>> HtmlInspector('<p><a href="/Category/Sample_Cat">Cat</a><img src="/I/pic.png"/></p>').extract_category_and_image_paths()
        (['Category/Sample_Cat'], ['I/pic.png'])
        """
        category_paths = []
        image_paths = []

        for a in self.soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("/"):
                href = href[1:]
            if href.startswith("Category/"):
                path = href.split("#")[0].split("?")[0]
                if path and path not in category_paths:
                    category_paths.append(path)

        for img in self.soup.find_all("img", src=True):
            src = img["src"].strip()
            if src.startswith("/"):
                src = src[1:]
            path = src.split("#")[0].split("?")[0]
            if path and path not in image_paths:
                image_paths.append(path)

        return category_paths, image_paths
