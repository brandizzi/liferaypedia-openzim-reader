"""
Liferay sign-in and related account actions via Playwright.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page


class LoginExecutor:
    """
    Performs Liferay login flows on a Playwright page.

    The page should belong to a browser context whose ``base_url`` is the
    portal origin (for example via ``browser.new_context(base_url=...)``) so
    relative navigations like ``/c/portal/login`` resolve correctly.
    """

    DEFAULT_TRIAL_PASSWORD = "test"

    def __init__(self, page: Page) -> None:
        self.page = page

    def login(self, username: str, password: str) -> None:
        """
        Try the default password ``test`` first. If that succeeds and the page
        shows **Change Password**, Liferay is assumed to show a dedicated form
        with **new password** and **retype** fields; that form is submitted
        with ``password``. If ``test`` fails, sign in with ``password`` instead.
        """
        self._submit_login_credentials(username, self.DEFAULT_TRIAL_PASSWORD)
        if self._change_password_prompt_visible():
            self._submit_password_redefinition_form(new_password=password)
            return

        self._submit_login_credentials(username, password)
        if not self._login_left_login_page():
            raise RuntimeError(
                "Login failed: neither the default password 'test' nor the "
                "configured password was accepted."
            )

    def _login_left_login_page(self) -> bool:
        return "portal/login" not in self.page.url.lower()

    def _change_password_prompt_visible(self) -> bool:
        """True when Liferay shows an actionable *Change Password* affordance."""
        page = self.page
        for loc in (
            page.get_by_role("link", name=re.compile(r"change\s+password", re.I)),
            page.get_by_role("button", name=re.compile(r"change\s+password", re.I)),
            page.get_by_text(re.compile(r"change\s+password", re.I)),
        ):
            if loc.count() and loc.first.is_visible():
                return True
        try:
            page.get_by_text(re.compile(r"change\s+password", re.I)).first.wait_for(
                state="visible", timeout=3000
            )
            print("Change password prompt visible")
            return True
        except Exception:
            return False

    def _submit_login_credentials(self, username: str, password: str) -> None:
        print("Submitting login credentials")
        self.page.goto("/c/portal/login", wait_until="domcontentloaded")
        login_input = self.page.locator('input[name$="_login"]').first
        password_input = self.page.locator('input[type="password"]').first
        login_input.wait_for(state="visible")
        login_input.fill(username)
        password_input.fill(password)
        form = self.page.locator("form").filter(
            has=self.page.locator('input[type="password"]')
        ).first
        submit = form.locator('button[type="submit"], input[type="submit"]').first
        submit.click()
        self.page.wait_for_load_state("networkidle")

    def _submit_password_redefinition_form(self, new_password: str) -> None:
        """Fill the post-login password form (new + retype) and submit."""
        print("Submitting password redefinition form")
        page = self.page
        form = page.locator("form").filter(has=page.locator('input[type="password"]')).first
        fields = form.locator('input[type="password"]')
        if fields.count() >= 2:
            fields.nth(0).wait_for(state="visible", timeout=15000)
            fields.nth(0).fill(new_password)
            fields.nth(1).fill(new_password)
        else:
            new_box = page.get_by_label(re.compile(r"new\s+password", re.I))
            if new_box.count() == 0:
                new_box = page.get_by_label(re.compile(r"^password$", re.I))
            repeat_box = page.get_by_label(
                re.compile(
                    r"repeat|re-?enter|retype|confirm|verify",
                    re.I,
                )
            )
            new_box.first.wait_for(state="visible", timeout=15000)
            new_box.first.fill(new_password)
            if repeat_box.count() == 0:
                raise RuntimeError(
                    "Could not find the retype/confirm password field on the "
                    "redefinition form."
                )
            repeat_box.first.fill(new_password)

        btn = form.locator('button[type="submit"], input[type="submit"]').first
        if btn.count() == 0:
            btn = page.get_by_role(
                "button", name=re.compile(r"save|submit|update", re.I)
            ).first
        btn.click()
        page.wait_for_load_state("networkidle")
