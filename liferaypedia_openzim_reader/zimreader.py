#!/usr bin env python
"""
General OpenZIM parsing functions for the LiferayPedia OpenZIM Reader package.

This module contains functions for parsing OpenZIM files, extracting entries,
and determining entry types and namespaces.
"""

import base64
import json

from libzim.reader import Archive

from liferaypedia_openzim_reader.htmlinspector import is_redirect_by_meta_tag, get_main_content

def extract_zim_to_json(zim_path: str, output_json: str, max_objects: int = 40):
    """
    Extract entries from a ZIM file to JSON format.
    
    Args:
        zim_path: Path to the input ZIM file
        output_json: Path to the output JSON file
        max_objects: Maximum number of objects to extract (default: 40)
    """
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
            print(f'skipping entry {entry_id}: {e}')
            continue

        if to_skip(entry):
            print(f'skipping {item.title}')
            continue

        raw_content = bytes(item.content)

        if item.mimetype.startswith("text"):
            content = raw_content.decode("utf-8", errors="replace")
        else:
            content = base64.b64encode(raw_content).decode("ascii")

        if is_redirect_by_meta_tag(content):
            print(f'skipping {item.title}')
            continue

        print(f'got {item.title}')
        entry_path = entry.path

        entry_type, namespace = get_entry_type_and_namespace(entry_path)

        if entry_type in {'article', 'category'}:
            content = get_main_content(content)

        results.append({
            "id": entry_id,
            "path": entry.path,
            "title": entry.title,
            "type": entry_type,
            "mime_type": item.mimetype,
            "is_redirect": entry.is_redirect,
            "namespace": namespace,
            "content": content,
            "size_bytes": item.size,
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

    In it, the namespace typically the first character before '/':

    >>> deduce_namespace('I/cat.png')
    'I'

    When there is no such character before '/' or it is '-', then it is in the
    main namespace:

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
        ...     def __init__(self, mimetype='text/html'):
        ...         self.mimetype = mimetype
        >>> class TestEntry:
        ...     def __init__(self, is_redirect=False, mime_type='text/html'):
        ...         self.is_redirect = is_redirect
        ...         self.item = TestItem(mime_type)
        ...     def get_item(self):
        ...         return self.item
        >>> to_skip(TestEntry(mime_type='application/javascript'))
        True

    - Redirects::
        >>> to_skip(TestEntry(is_redirect=True, mime_type='text/html'))
        True

    **NOTE**: When a redirect points to a section of another page, instead of
    the page, it is not marked as redirect. So we have to check their  meta tags
    for redirect pragmas. This is *not* done in this function, but later, when
    we already have the parsed content to examine, for performance reasons.

    In all other cases, it should return False::

    >>> to_skip(TestEntry(is_redirect=False, mime_type='text/html'))
    False
    """
    item = entry.get_item()
    if entry.is_redirect:
        return True

    if item.mimetype == 'application/javascript':
        return True

    return False
