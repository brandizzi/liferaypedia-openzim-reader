"""
Liferay portal access via the browser using Playwright.
"""

from __future__ import annotations

from typing import Sequence

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from liferaypedia_liferay_user.login_executor import LoginExecutor
from liferaypedia_liferay_user.web_content_executor import WebContentExecutor


class LiferayWebUser:
    """
    Opens a Liferay portal in a browser and signs in with the given credentials.

    ``url`` should be the portal origin (for example ``https://portal.example.com``).
    :meth:`login` delegates to :class:`LoginExecutor`, which tries the default
    password ``test`` first. When that works, if the portal shows **Change
    Password**, it fills the automatic new-password / retype form with the
    constructor password; if ``test`` is rejected, it signs in with the
    constructor password instead.
    The browser context uses ``base_url`` so login paths resolve correctly.

    :meth:`post_web_content` delegates to :class:`WebContentExecutor`.
    """

    def __init__(self, url: str, username: str, password: str) -> None:
        self.base_url = url.rstrip("/")
        self.username = username
        self.password = password
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    def login(self) -> None:
        """Launch a browser (if needed) and sign in via :class:`LoginExecutor`."""
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            context = self.browser.new_context(base_url=self.base_url)
            self.page = context.new_page()

        assert self.page is not None
        LoginExecutor(self.page).login(self.username, self.password)

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
        In the already-authenticated browser session, create web content via
        :class:`WebContentExecutor`.

        ``site_friendly_url`` is used to open the site home
        (``/web/{site}/home``) so the **Product Menu** is available.

        ``categories`` are **labels as shown in the Categorization** section
        (checkboxes or row titles), not numeric IDs.
        """
        if self.page is None:
            raise RuntimeError("Call login() before post_web_content().")
        WebContentExecutor(self.page).post_web_content(
            title,
            content,
            friendly_url,
            categories,
            site_friendly_url=site_friendly_url,
        )

    def close(self) -> None:
        """Close the browser and stop Playwright."""
        if self.browser is not None:
            self.browser.close()
            self.browser = None
        self.page = None
        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None
