# tests/test_behavior_oracle.py
import json
import os
from pathlib import Path
from typing import Optional

import pytest
from playwright.sync_api import Page, expect

# --- Konfiguracja i dane ---
BEHAVIOR_ORACLES_PATH = Path(__file__).parent / "behavior_oracles.json"
with open(BEHAVIOR_ORACLES_PATH, "r", encoding="utf-8") as f:
    behavior_oracles = json.load(f)

# Pozwala uruchomić te same scenariusze na prod i lokalnie
# Przykład: BASE_URL=https://printworks.pl pytest -k behavior_oracle
BASE_URL = os.getenv("BASE_URL", "http://localtest.me")
DEBUG = os.getenv("DEBUG_BEHAVIOR", "0") == "1"


# --- Utilsy ---


def expand_vars(s: Optional[str]) -> Optional[str]:
    """W JSON możesz pisać np. {{BASE_URL}}/pl – tutaj to rozwiniemy."""
    if not s:
        return s
    return s.replace("{{BASE_URL}}", BASE_URL)


def _first_existing_locator(page: Page, selector: str):
    """
    Obsługa selektora w formie 'sel1 || sel2 || sel3'.
    Zwraca pierwszy istniejący locator.
    """
    candidates = [part.strip() for part in selector.split("||")]
    for sel in candidates:
        loc = page.locator(sel)
        if loc.count() > 0:
            return loc
    # jeśli nic nie istnieje, zwróć locator pierwszego — pozwoli uzyskać czytelny błąd Playwrighta
    return page.locator(candidates[0])


def _resolve_locator(page: Page, selector: str):
    """
    Zawsze zwraca TYLKO jeden element:
    - jeśli podano 'sel1 || sel2', wybiera pierwszy istniejący
    - jeśli selektor zwraca wiele elementów, bierze .first
    """
    if "||" in selector:
        loc = _first_existing_locator(page, selector)
    else:
        loc = page.locator(selector)
    # gwarancja pojedynczości, by uniknąć strict=True errors
    return loc.first


def _maybe_debug(page: Page, name: str):
    if not DEBUG:
        return
    Path(f"debug_{name}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=f"debug_{name}.png")


def prepare_test_data(oracles):
    return [pytest.param(story["story_name"], story["steps"], id=story["story_name"]) for story in oracles]


# --- Test właściwy ---


@pytest.mark.skip(reason="Requires local test server")
@pytest.mark.parametrize("story_name, steps", prepare_test_data(behavior_oracles))
def test_behavior_oracle(page: Page, story_name: str, steps: list):
    print(f"Running story: {story_name}")

    for step in steps:
        action = step.get("action")
        selector = step.get("selector")
        value = step.get("value")
        raw_url = step.get("url")
        url = expand_vars(raw_url)
        assertion = step.get("assertion")

        print(f"- Executing step: {action}")

        if action == "goto":
            if not url:
                raise ValueError(f"Step 'goto' requires a non-empty url in story '{story_name}'")
            page.goto(url)
            # Przy AngularJS zwykle warto dać chwilę na inicjalizację routingu:
            # (nie używam tu 'networkidle', bo bywa mylące przy SPA)
            _maybe_debug(page, "goto")

        elif action == "click":
            if not selector:
                raise ValueError(f"Step 'click' requires 'selector' in story '{story_name}'")
            _resolve_locator(page, selector).click()
            _maybe_debug(page, "after_click")

        elif action == "fill":
            if not selector:
                raise ValueError(f"Step 'fill' requires 'selector' in story '{story_name}'")
            if value is None:
                raise ValueError(f"Step 'fill' requires 'value' in story '{story_name}'")
            # zabezpieczenie przed strict=True i wieloma polami o tym samym selektorze
            _resolve_locator(page, selector).fill(str(value))

        elif action == "wait_for_selector":
            if not selector:
                raise ValueError(f"Step 'wait_for_selector' requires 'selector' in story '{story_name}'")
            if "||" in selector:
                # czekamy aż którykolwiek z wariantów się pojawi (visible)
                variants = [s.strip() for s in selector.split("||")]
                # zainicjuj oczekiwanie na pierwszy, by złapać timeout, jeśli nic się nie pojawi
                for sel in variants:
                    try:
                        _resolve_locator(page, sel).wait_for(state="visible")
                        break
                    except Exception:
                        continue
                else:
                    # nic nie „wyszło”
                    _resolve_locator(page, variants[0]).wait_for(state="visible")
            else:
                _resolve_locator(page, selector).wait_for(state="visible")
            _maybe_debug(page, "after_wait_for_selector")

        elif action == "wait_for_url":
            if not url:
                raise ValueError(f"Step 'wait_for_url' requires 'url' in story '{story_name}'")
            # W SPA stabilniejsze niż page.wait_for_url():
            expect(page).to_have_url(url)
            _maybe_debug(page, "after_wait_for_url")

        elif action == "expect":
            if not selector:
                raise ValueError(f"Step 'expect' requires 'selector' in story '{story_name}'")
            loc = _resolve_locator(page, selector)

            if assertion == "visible":
                expect(loc).to_be_visible()
            elif assertion == "hidden":
                expect(loc).to_be_hidden()
            elif assertion == "count":
                expect(loc).to_have_count(int(value))
            elif assertion == "contains_text":
                expect(loc).to_contain_text(str(value))
            else:
                raise ValueError(f"Unknown assertion type: {assertion}")

        else:
            raise ValueError(f"Unknown action type: {action}")
