#!/usr/bin/env python3
"""
Generate a minimal OpenZIM file containing:
  - One article (with an image and a category link)
  - The image blob
  - A category page
  - A redirect that points to the article

Path conventions match liferaypedia_openzim_reader (A/ article, I/ image, Category/).
Run with the project virtualenv:
  ~/lib/virtualenv/liferaypedia-openzim-reader/bin/python generate_sample_zim.py [output.zim]
"""

import argparse
import base64
import os
import sys
import tempfile

from libzim.writer import Creator, FileProvider, Hint, Item, StringProvider


# Minimal 1x1 PNG (valid PNG bytes)
MINIMAL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MINIMAL_PNG = base64.b64decode(MINIMAL_PNG_B64)


class ZimItem(Item):
    """Item that serves string content with a given mimetype."""

    def __init__(self, path: str, title: str, content: bytes | str, mimetype: str, hints: dict | None = None):
        super().__init__()
        self._path = path
        self._title = title
        self._content = content.encode("utf-8") if isinstance(content, str) else content
        self._mimetype = mimetype
        self._hints = hints or {}

    def get_path(self):
        return self._path

    def get_title(self):
        return self._title

    def get_mimetype(self):
        return self._mimetype

    def get_contentprovider(self):
        return StringProvider(self._content.decode("utf-8", errors="replace"))

    def get_hints(self):
        return self._hints


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a sample OpenZIM with article, image, category, redirect.")
    parser.add_argument(
        "output",
        nargs="?",
        default="sample.zim",
        help="Output ZIM path (default: sample.zim)",
    )
    args = parser.parse_args()

    article_path = "A/Sample_Article"
    image_path = "I/sample.png"
    category_path = "Category/Sample_Category"
    redirect_path = "-/Redirect_Here"  # redirect from main namespace to article

    article_html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Sample Article</title></head>
<body>
<main>
<h1>Sample Article</h1>
<p>This article contains an image and a category link.</p>
<figure>
  <img src="/{image_path}" alt="Sample image" />
  <figcaption>Sample image</figcaption>
  <h1 id="fake_section">Fake section</h1>
</figure>
<p>Category: <a href="/{category_path}">Sample Category</a></p>
</main>
</body>
</html>"""

    category_html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Sample Category</title></head>
<body>
<main>
<h1>Category: Sample Category</h1>
<ul>
  <li><a href="/{article_path}">Sample Article</a></li>
</ul>
</main>
</body>
</html>"""

    section_redirect_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;{article_path}"
<title>Sample Article</title></head>
<body>
<main>
<h1><a href="{article_path}#fake_section">Fake Section</a></h1>
</main>
</body>
</html>"""

    class FileItem(Item):
        """Item that serves content from a file (for binary blobs like images)."""

        def __init__(self, path: str, title: str, fpath: str, mimetype: str):
            super().__init__()
            self._path = path
            self._title = title
            self._fpath = fpath
            self._mimetype = mimetype

        def get_path(self):
            return self._path

        def get_title(self):
            return self._title

        def get_mimetype(self):
            return self._mimetype

        def get_contentprovider(self):
            return FileProvider(self._fpath)

        def get_hints(self):
            return {}

    article_item = ZimItem(
        article_path, "Sample Article", article_html, "text/html",
        hints={Hint.FRONT_ARTICLE: True},
    )
    category_item = ZimItem(category_path, "Sample Category", category_html, "text/html")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(MINIMAL_PNG)
        tmp_path = tmp.name
    try:
        image_item = FileItem(image_path, "sample.png", tmp_path, "image/png")

        with Creator(args.output).config_indexing(True, "eng") as creator:
            creator.set_mainpath(article_path)
            creator.add_item(article_item)
            creator.add_item(image_item)
            creator.add_item(category_item)
            creator.add_redirection(redirect_path, "Redirect Here", article_path, {})
            for name, value in (
                ("Creator", "generate_sample_zim.py"),
                ("Description", "Sample ZIM with article, image, category, redirect"),
                ("Name", "sample-zim"),
                ("Title", "Sample ZIM"),
                ("Language", "eng"),
            ):
                creator.add_metadata(name, value)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
