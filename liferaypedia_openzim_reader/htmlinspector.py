# liferaypedia_openzim_reader/html_parser.py
"""
HTML parsing functions for the LiferayPedia OpenZIM Reader package.

This module contains functions for parsing HTML content, extracting main content,
and detecting redirect meta tags.
"""

from bs4 import BeautifulSoup

def get_main_content(content):
    """
    Return the content from the <main> element in a string-encoded HTML
    document. content may be str or a BeautifulSoup instance::

    >>> get_main_content('''
    ... <html>
    ...     <body>
    ...         <ul><li>A</li></ul>
    ...         <main>
    ...             <h1>Title</h1><p>Text</p>
    ...         </main>
    ...     </body>
    ... </html>
    ... ''')
    '<h1>Title</h1><p>Text</p>'
    """
    soup = content if isinstance(content, BeautifulSoup) else BeautifulSoup(content, 'html.parser')
    main = soup.find('main')
    return main.decode_contents().strip() if main else ''


def is_redirect_by_meta_tag(content):
    """
    Check if an HTML document contains a meta tag that causes page to refresh.
    content may be str or a BeautifulSoup instance::

    >>> is_redirect_by_meta_tag('''
    ... <!DOCTYPE html><html><head><meta http-equiv="refresh" content="5"></head></html>
    ... ''')
    True

    It should be case-insensitive::

    >>> is_redirect_by_meta_tag('''
    ... <html>head><meta HTTP-EQUIV="REFRESH" content="5"></head></html>
    ... ''')
    True

    Of course, it should return false if there is no meta tag, or if there are
    meta tags that do not refresh, or if there is no content on it::

    >>> is_redirect_by_meta_tag('''
    ... <html><head><title>Test</title></head></html>
    ... ''')
    False
    >>> is_redirect_by_meta_tag('''
    ... html><head<><meta charset="UTF-8"><title>Test</title></head></html>
    ... ''')
    False
    >>> is_redirect_by_meta_tag('''
    ... <html><head><meta http-equiv="refresh"></head></html>
    ... ''')
    False
    >>> empty_html = ''
    >>> is_redirect_by_meta_tag(empty_html)
    False
    """
    soup = content if isinstance(content, BeautifulSoup) else BeautifulSoup(content, 'html.parser')

    head = soup.find('head')
    meta_tags = soup.find_all('meta')

    for meta in meta_tags:
        http_equiv = meta.get('http-equiv', '').lower()
        if http_equiv == 'refresh':
            # Check if content attribute exists (required for refresh)
            content = meta.get('content', '')
            if content:
                return True

    return False


def extract_category_and_image_paths(content) -> tuple[list[str], list[str]]:
    """
    Extract category and image paths from HTML content.

    Returns (category_paths, image_paths) where each path is in ZIM format
    (e.g. "Category/Name", "I/filename.png"). Only for use with article content.
    content may be str or a BeautifulSoup instance (or Tag)::

    >>> html = '<p><a href="/Category/Sample_Cat">Cat</a><img src="/I/pic.png"/></p>'
    >>> extract_category_and_image_paths(html)
    (['Category/Sample_Cat'], ['I/pic.png'])
    """
    root = content if not isinstance(content, str) else BeautifulSoup(content, 'html.parser')
    category_paths = []
    image_paths = []

    for a in root.find_all('a', href=True):
        href = a['href'].strip()
        if href.startswith('/'):
            href = href[1:]
        if href.startswith('Category/'):
            path = href.split('#')[0].split('?')[0]
            if path and path not in category_paths:
                category_paths.append(path)

    for img in root.find_all('img', src=True):
        src = img['src'].strip()
        if src.startswith('/'):
            src = src[1:]
        path = src.split('#')[0].split('?')[0]
        if path and path not in image_paths:
            image_paths.append(path)

    return category_paths, image_paths
