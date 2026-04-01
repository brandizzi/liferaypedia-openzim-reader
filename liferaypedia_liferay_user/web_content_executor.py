"""
Create Liferay web content articles via the Journal UI (Playwright).
"""

from __future__ import annotations

import re
import time
from typing import Sequence

from playwright.sync_api import Page


class WebContentExecutor:
    """
    Automates **Basic Web Content** creation in the Liferay product menu.

    The page should belong to a browser context whose ``base_url`` is the
    portal origin so paths like ``/web/guest/home`` resolve correctly.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    def post_web_content(
        self,
        title: str,
        content: str,
        friendly_url: str,
        categories: Sequence[str],
        *,
        site_friendly_url: str = "guest",
    ) -> None:
        """
        Open the site home, use **Content & Data → Web Content**, start Basic
        Web Content, fill fields, optionally set categories, and publish.

        ``categories`` are labels as shown in the Categorization section.
        """
        slug = friendly_url.strip().lstrip("/")
        page = self.page
        page.goto(f"/web/{site_friendly_url}/home", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        self._navigate_via_product_menu()
        self._open_new_basic()
        self._fill_title(title)
        self._fill_body(content)
        self._fill_friendly_url(slug)
        self._apply_categories(categories)
        self._publish()

    def _navigate_via_product_menu(self) -> None:
        page = self.page
        toggle = page.locator(".product-menu-toggle").first
        toggle.wait_for(state="visible", timeout=15000)
        toggle.click()
        content_data = page.get_by_text(
            re.compile(r"content\s*&\s*data", re.I),
        ).first
        content_data.wait_for(state="visible", timeout=15000)
        content_data.click()
        web = page.get_by_role("link", name=re.compile(r"^\s*web content\s*$", re.I))
        if web.count() == 0:
            web = page.get_by_role("menuitem", name=re.compile(r"web content", re.I))
        if web.count() == 0:
            web = page.locator("a").filter(
                has_text=re.compile(r"^\s*web content\s*$", re.I)
            )
        web.first.wait_for(state="visible", timeout=15000)
        web.first.click()
        page.wait_for_load_state("networkidle")

    def _open_new_basic(self) -> None:
        page = self.page
        new_btn = page.get_by_role("button", name=re.compile(r"^\s*new\s*$", re.I))
        if new_btn.count() == 0:
            new_btn = page.get_by_role("button", name=re.compile(r"new", re.I))
        new_btn.first.click()
        basic_re = re.compile(r"basic\s+web\s+content", re.I)
        for role in ("menuitem", "option", "link"):
            choice = page.get_by_role(role, name=basic_re)
            if choice.count():
                choice.first.click()
                break
        else:
            page.get_by_text(basic_re).first.click()
        page.wait_for_load_state("domcontentloaded")
        self._wait_wysiwyg_editor(page)

    def _fill_title(self, title: str) -> None:
        page = self.page
        title_box = page.get_by_role("textbox", name=re.compile(r"title", re.I))
        if title_box.count() == 0:
            title_box = page.get_by_label(re.compile(r"title", re.I))
        title_box.first.wait_for(state="visible")
        title_box.first.fill(title)

    def _fill_body(self, html: str) -> None:
        page = self.page
        iframe = self._wait_wysiwyg_editor(page)
        if iframe.count():
            iframe.wait_for(state="attached")
            frame = page.frame_locator("iframe.cke_wysiwyg_frame").first
            body = frame.locator("body")
            body.wait_for(state="attached")
            body.evaluate(
                """(el, html) => { el.innerHTML = html; }""",
                html,
            )
            return

        editable = page.locator(
            '[contenteditable="true"], .cke_editable[contenteditable="true"]'
        ).first
        if editable.count():
            editable.wait_for(state="visible")
            editable.evaluate(
                """(el, html) => { el.innerHTML = html; }""",
                html,
            )
            return

        raise RuntimeError(
            "Could not find the web content body editor (CKEditor iframe or contenteditable)."
        )

    def _wait_wysiwyg_editor(self, page: Page) -> Locator:
        for _ in range(5):
            iframe = page.locator("iframe.cke_wysiwyg_frame").first
            if iframe.count():
                return iframe
            time.sleep(1)
        raise RuntimeError("Could not find the CKEditor iframe.")

    def _fill_friendly_url(self, slug: str) -> None:
        page = self.page
        friendly = page.locator(
            'input[name*="friendlyURL" i], input[id*="FriendlyURL" i], '
            'input[name*="friendlyUrl" i]'
        ).first
        if friendly.count() == 0:
            friendly = page.get_by_label(re.compile(r"friendly\s*url", re.I))
        if friendly.count() == 0:
            self._expand_panel(re.compile(r"configuration|display|seo", re.I))
            friendly = page.locator(
                'input[name*="friendlyURL" i], input[id*="FriendlyURL" i]'
            ).first
        if friendly.count() == 0:
            raise RuntimeError("Could not find the Friendly URL field.")
        friendly.wait_for(state="visible")
        friendly.fill(slug)

    def _expand_panel(self, title_re: re.Pattern[str]) -> None:
        page = self.page
        header = page.locator("button, .panel-header, .panel-title").filter(
            has_text=title_re
        )
        if header.count():
            header.first.click(timeout=5000)

    def _apply_categories(self, categories: Sequence[str]) -> None:
        if not categories:
            return
        page = self.page
        self._expand_panel(re.compile(r"categorization|categories", re.I))
        for cat in categories:
            box = page.get_by_role(
                "checkbox", name=re.compile(rf"^\s*{re.escape(cat)}\s*$", re.I)
            )
            if box.count() == 0:
                box = page.get_by_role("checkbox", name=re.escape(cat))
            if box.count() == 0:
                raise RuntimeError(f"Could not find category checkbox for {cat!r}.")
            box.first.check()

    def _publish(self) -> None:
        page = self.page
        breakpoint()
        for label in ("Publish", "Submit for Publication"):
            btn = page.get_by_role(
                "button", name=re.compile(rf"^\s*{re.escape(label)}\s*$", re.I)
            )
            if btn.count() and btn.first.is_enabled():
                btn.first.click()
                page.wait_for_load_state("networkidle")
                return
        raise RuntimeError(
            "Could not find a Publish or Submit for Publication button (workflow may differ)."
        )
