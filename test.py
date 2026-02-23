import json
import base64
from libzim.reader import Archive


def extract_zim_to_json(zim_path: str, output_json: str, max_objects: int = 40):
    zim = Archive(zim_path)

    results = []
    total = zim.entry_count
    limit = min(max_objects, total)
    entry_id = 0
    count = 0

    while count < limit:
        entry_id += 1
        try:
            entry = zim._get_entry_by_id(entry_id)
            item = entry.get_item()
        except Exception as e:
            print(f'Skipping entry {entry_id} due to error: {e}')
            continue

        if to_skip(entry):
            continue

        raw_content = bytes(item.content)

        if item.mimetype.startswith("text"):
            content = raw_content.decode("utf-8", errors="replace")
        else:
            content = base64.b64encode(raw_content).decode("ascii")

        entry_path = entry.path

        entry_type, namespace = get_entry_type_and_namespace(entry_path)

        results.append({
            "id": entry_id,
            "path": entry.path,
            "title": entry.title,
            "type": entry_type,
            "mime_type": item.mimetype,
            "is_redirect": entry.is_redirect,
            "namespace": namespace,
            "content": content,
            "size_bytes": item.size
        })
        count += 1

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(results)} entries to {output_json}")
    print(f"Namespaces found: {set(item['namespace'] for item in results)}")
    print(f"Types found: {set(item['type'] for item in results)}")

def deduce_namespace(entry_path):
    """
    Given the path to the entry, deduce the namespace_part

    OpenZIM paths typically follow patterns like:
    - A/Article for articles
    - I/Image for images
    - -/ for main namespace
    - / for main namespace
        entry_path = entry.path

    In it, the namespace typically the first character before '/'::

    >>> deduce_namespace('I/cat.png')
    'I'

    When there is no such character before '/' or it is '-', then it is in the
    main namespace::

    >>> deduce_namespace('-/Main_Page')
    'main'
    >>> deduce_namespace('/Entry')
    'main'

    This function returns 'main' by default anyway:

    >>> deduce_namespace('lostmedia')
    'main'
    """
    namespace = "main"

    if entry_path.startswith('-/') or entry_path.startswith('/'):
        namespace = "main"
    elif '/' in entry_path:
        namespace_part = entry_path.split('/')[0]
        if namespace_part and namespace_part != '-':
            namespace = namespace_part

    return namespace

def get_entry_type_and_namespace(entry_path):
    """
    Given a path to an entry, this function returns both the entry type and
    the namespace.

    For the most common page-like entries, it will define the entry type from
    the namespace::

    >>> get_entry_type_and_namespace('-/Main_Page')
    ('page', 'main')
    >>> get_entry_type_and_namespace('A/Bobsled')
    ('article', 'A')
    >>> get_entry_type_and_namespace('humanities.jpg')
    ('page', 'main')
    >>> get_entry_type_and_namespace('-/Main_Page')
    ('page', 'main')
    >>> get_entry_type_and_namespace('I/cat.png')
    ('image', 'I')
    >>> get_entry_type_and_namespace('I/cat.mp4')
    ('image', 'I')


    If the namespace is File, then we check to see the kind of file from
    the extension:

    >>> get_entry_type_and_namespace('File/cat.png')
    ('image', 'File')
    >>> get_entry_type_and_namespace('File/novel.pdf')
    ('document', 'File')
    >>> get_entry_type_and_namespace('File/jazz.ogg')
    ('audio', 'File')

    """
    namespace = deduce_namespace(entry_path)

    entry_type = "unknown"
    if namespace == "main":
        entry_type = "page"
    elif namespace == "A":
        entry_type = "article"
    elif namespace == "I":
        entry_type = "image"
    elif namespace == "Category":
        entry_type = "category"
    elif namespace == "Discussion":
        entry_type = "discussion"
    elif namespace == "File":
        entry_type = "file"
    elif namespace == "Template":
        entry_type = "template"
    elif namespace == "Help":
        entry_type = "help"
    elif namespace == "Portal":
        entry_type = "portal"
    elif namespace == "Book":
        entry_type = "book"
    elif namespace == "MediaWiki":
        entry_type = "mediawiki"

    # Additional type detection based on file extension
    if namespace == 'File':
        extension = entry_path.split('.')[-1].lower()
        if extension in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
            entry_type = "image"
        elif extension in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
            entry_type = "document"
        elif extension in ['mp3', 'wav', 'ogg', 'flac', 'aac']:
            entry_type = "audio"
        elif extension in ['mp4', 'avi', 'mov', 'wmv', 'flv']:
            entry_type = "video"
        elif extension in ['zip', 'rar', '7z', 'tar', 'gz']:
            entry_type = "archive"

    return entry_type, namespace

def to_skip(entry):
    """
    Decides if a specific entry should be
    skipped. We skip the following of entries right now:

    - JavaScript files::

        >>> class TestItem:
        ...     def __init__(self, mimetype='text/html', content='hello'):
        ...         self.mimetype = mimetype
        ...         self.content = content
        >>> class TestEntry:
        ...     def __init__(self, is_redirect=False, mime_type='text/html', content='hello'):
        ...         self.is_redirect = is_redirect
        ...         self.item = TestItem(mime_type, content)
        ...     def get_item(self):
        ...         return self.item
        >>> to_skip(TestEntry(mime_type='application/javascript'))
        True

    - Redirects::
        >>> to_skip(TestEntry(is_redirect=True, mime_type='text/html'))
        True

        - When a redirect points to a section of another page, instead of the
          page, it is not marked as redirect. So we have to check their
          meta tags for redirect pragmas:

            >>> to_skip(TestEntry(content='<head><meta http-equiv="refresh" content="5"></head>'))
            True

    In all other cases, it should return False::

    >>> to_skip(TestEntry(is_redirect=False, mime_type='text/html'))
    False
    """
    item = entry.get_item()
    if entry.is_redirect:
        return True


    if item.mimetype == 'application/javascript':
        return True

    if is_redirect_by_meta_tag(item.content):
        return True

    return False

from bs4 import BeautifulSoup

def is_redirect_by_meta_tag(html_content):
    """
    Check if an HTML document contains a meta tag that causes page to refresh::

    >>> is_redirect_by_meta_tag('''
    ... <!DOCTYPE html><html><head><meta http-equiv="refresh" content="5"></head></html>
    ... ''')
    True

    It should be case-insensitive::

    >>> is_redirect_by_meta_tag('''
    ... <html><head><meta HTTP-EQUIV="REFRESH" content="5"></head></html>
    ... ''')
    True

    Of course, it should return false if there is no meta tag, or if there are
    meta tags that do not refresh, or if there is no content on it::

    >>> is_redirect_by_meta_tag('''
    ... <html><head><title>Test</title></head></html>
    ... ''')
    False
    >>> is_redirect_by_meta_tag('''
    ... <html><head><meta charset="UTF-8"><title>Test</title></head></html>
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
    soup = BeautifulSoup(html_content, 'html.parser')

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



if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python zim_to_json.py <input.zim> <output.json>")
        sys.exit(1)

    extract_zim_to_json(sys.argv[1], sys.argv[2], max_objects=40)
