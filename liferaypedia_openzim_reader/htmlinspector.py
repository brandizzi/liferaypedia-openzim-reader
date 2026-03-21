# liferaypedia_openzim_reader/html_parser.py
"""
HTML parsing functions for the LiferayPedia OpenZIM Reader package.

This module provides the HtmlInspector class for parsing HTML content,
extracting main content, and detecting redirect meta tags.
"""

from urllib.parse import parse_qs, unquote, urlparse

from bs4 import BeautifulSoup


def _normalize_category_title_for_zim(name: str) -> str:
    """
    Turn a category title fragment into a ZIM-style segment (spaces → underscores).

    >>> _normalize_category_title_for_zim("Foo Bar")
    'Foo_Bar'
    """
    return name.replace(" ", "_")


def href_to_category_zim_path(href: str):
    """
    If ``href`` points at a wiki category page, return ``Category/Title`` (ZIM-style);
    otherwise return ``None``.

    Accepts ZIM-style ``Category/...``, MediaWiki ``Category:...``, and absolute
    ``https://.../wiki/Category:...`` URLs (any host).

    It should return the correct ZIM-style path given a full URL to a mediawiki page:

    >>> href_to_category_zim_path("https://en.wikipedia.org/wiki/Category:Foo?q=1")
    'Category/Foo'

    It should also return a proper path given namespaced syntaxes, both with a colon:
    >>> href_to_category_zim_path("Category:Foo")
    'Category/Foo'

    ...and with slashes::

    >>> href_to_category_zim_path("Category/Foo")
    'Category/Foo'

    Note that the path is normalized to ZIM-style, so spaces are replaced with underscores.

    >>> href_to_category_zim_path("Category/Foo Bar")
    'Category/Foo_Bar'

    If the path is a category page with a slash, then the whole path is returned::

    >>> href_to_category_zim_path("Category/Foo/Bar")
    'Category/Foo/Bar'

    It should return None if the href is not a category page:

    >>> href_to_category_zim_path("https://en.wikipedia.org/wiki/Foo?q=1") is None
    True
    """
    if not href:
        return None
    raw = href.strip()
    low = raw.lower()
    if low.startswith(("#", "javascript:", "mailto:")):
        return None

    base = raw.split("#")[0].split("?")[0]
    base = unquote(base)
    if base.startswith("//"):
        base = "https:" + base

    if base.startswith(("http://", "https://")):
        parsed = urlparse(base)
        if "index.php" in (parsed.path or "") and parsed.query:
            for t in parse_qs(parsed.query, keep_blank_values=True).get("title", []):
                t = unquote(t.replace("+", " "))
                if (zim_path := get_category_zim_path_from_title(t)) is not None:
                    return zim_path
            return None
        path = parsed.path or ""
        if "/wiki/" in path:
            segment = path.split("/wiki/", 1)[1]
            segment = unquote(segment.split("/")[0])
            if (zim_path :=  get_category_zim_path_from_title(segment)) is not None:
                return zim_path
        return None

    rel = base
    while rel.startswith("../"):
        rel = rel[3:]
    while rel.startswith("./"):
        rel = rel[2:]
    if rel.startswith("/"):
        rel = rel[1:]
    if rel.startswith("-/"):
        rel = rel[2:]
    if len(rel) >= 5 and rel[:5].lower() == "wiki/":
        rel = rel[5:]

    if (zim_path :=  get_category_zim_path_from_title(rel)) is not None:
        return zim_path
    return None

def is_category_title(title: str) -> bool:
    """
    Check if a title is a valid category title.

    >>> is_category_title("Category:Foo")
    True
    >>> is_category_title("Category/Foo")
    True
    >>> is_category_title("Category:Foo/Bar")
    True
    >>> is_category_title("Foo Bar")
    False
    """
    return (
        len(title) >= 9
        and  title[:8].lower() == "category"
        and title[8] in {":", "/"}
    )

def get_category_zim_path_from_title(title: str) -> str:
    """
    Get the ZIM-style path for a category title.

    >>> get_category_zim_path_from_title("Category:Foo")
    'Category/Foo'
    >>> get_category_zim_path_from_title("Category/Foo")
    'Category/Foo'
    >>> get_category_zim_path_from_title("Category:Foo/Bar")
    'Category/Foo/Bar'
    >>> get_category_zim_path_from_title("Foo Bar") is None
    True
    >>> get_category_zim_path_from_title("Category:") is None
    True
    >>> get_category_zim_path_from_title("Category:/Foo")
    'Category//Foo'
    >>> get_category_zim_path_from_title("Category:Foo")
    'Category/Foo'
    >>> get_category_zim_path_from_title("Category:Foo/Bar")
    'Category/Foo/Bar'
    """
    if not is_category_title(title):
        return None
    rest = title[9:]

    if not rest:
        return None

    return "Category/" + _normalize_category_title_for_zim(rest)

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

        Categories are taken from **the entire document** (including outside
        ``<main>``), e.g. MediaWiki ``#catlinks``. Each category is returned as a
        ZIM-style path ``Category/Title_with_underscores``.

        Image ``src`` values are collected from the whole document.

        Returns (category_paths, image_paths) where image paths are ZIM-style
        (e.g. ``I/filename.png``)::

        >>> HtmlInspector('<p><a href="/Category/Sample_Cat">Cat</a><img src="/I/pic.png"/></p>').extract_category_and_image_paths()
        (['Category/Sample_Cat'], ['I/pic.png'])

        MediaWiki ``Category:`` hrefs map to the same ZIM shape::

        >>> HtmlInspector('<footer><a href="./Category:Sample_Cat">c</a></footer>').extract_category_and_image_paths()
        (['Category/Sample_Cat'], [])

        Absolute wiki URLs are normalized::

        >>> HtmlInspector('<a href="https://en.wikipedia.org/wiki/Category:Foo_Bar">x</a>').extract_category_and_image_paths()
        (['Category/Foo_Bar'], [])

        Links outside ``<main>`` (e.g. category footers) are included::

        >>> HtmlInspector('<main><p>x</p></main><footer><a href="Category:Footer_Cat">c</a></footer>').extract_category_and_image_paths()
        (['Category/Footer_Cat'], [])
        """
        category_paths = []
        image_paths = []

        for a in self.soup.find_all("a", href=True):
            path = href_to_category_zim_path(a["href"])
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
