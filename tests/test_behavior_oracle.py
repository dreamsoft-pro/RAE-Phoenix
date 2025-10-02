import os
import re
import json
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

BEHAVIOR_ORACLES_PATH = Path(__file__).parent / "behavior_oracles.json"
with open(BEHAVIOR_ORACLES_PATH, "r", encoding="utf-8") as f:
    behavior_oracles = json.load(f)

# ------------- Konfiguracja hosta -------------
# Pozwala uruchomić te same scenariusze na prod i lokalnie
BASE_URL = os.getenv("BASE_URL", "http://localtest.me")

DEBUG = os.getenv("DEBUG_BEHAVIOR", "0") == "1"

def expand_vars(s: str | None) -> str | None:
    if not s:
        return s
    return s.replace("{{BASE_URL}}", BASE_URL)

def first_existing_locator(page: Page, selector: str):
    """
    Pozwala podać listę selektorów rozdzielonych '||' (NIE przecinkiem w CSS),
    a my zwracamy pierwszy istniejący. To bezpieczniejsze niż przecinki z strict=True.
    """
    parts = [p.strip() for p in selector.split("||")]
    for sel in parts:
        loc = page.locator(sel)
        if loc.count() > 0:
            return loc
    # jeśli nic nie weszło – zwracamy locator na pierwszy, by dostać czytelny błąd Playwrighta
    return page.locator(parts[0])

def prepare_test_data(oracles):
    data = []
    for story in oracles:
        data.append(pytest.param(story["story_name"], story["steps"], id=story["story_name"]))
    return data

@pytest.mark.parametrize("story_name, steps", prepare_test_data(behavior_oracles))
def test_behavior_oracle(page: Page, story_name: str, steps: list):
    print(f"Running story: {story_name}")

    for step in steps:
        action = step.get("action")
        raw_selector = step.get("selector")
        selector = raw_selector
        value = step.get("value")
        raw_url = step.get("url")
        url = expand_vars(raw_url)
        assertion = step.get("assertion")

        print(f"- Executing step: {action}")

        if action == "goto":
            goto_url = expand_vars(step["url"])
            if goto_url is None:
                raise ValueError(f"Step 'goto' requires a non-None url in story '{story_name}'")
            page.goto(goto_url)
            if DEBUG:
                page.screenshot(path="debug_goto.png")
                Path("debug_goto.html").write_text(page.content(), encoding="utf-8")

        elif action == "click":
            # BEZ debugowego bałaganu i bez psucia wcięć
            # Zawsze klikamy w kontekście strict=True (domyślnie)
            page.locator(selector).click()
            if DEBUG:
                page.screenshot(path="debug_after_click.png")
                Path("debug_after_click.html").write_text(page.content(), encoding="utf-8")

        elif action == "fill":
            # Nie używamy selektorów z przecinkiem – jeżeli potrzebujemy wariantów,
            # to dostarczamy je jako 'sel1 || sel2'
            if "||" in selector:
                first_existing_locator(page, selector).fill(value)
            else:
                page.locator(selector).fill(value)

        elif action == "wait_for_selector":
            # Akceptujemy listę wariantów przez '||'
            if "||" in selector:
                # czekamy aż któryś istnieje
                parts = [p.strip() for p in selector.split("||")]
                page.wait_for_selector(parts[0])  # start timer
                # sprawdzamy iteracyjnie
                found = False
                for sel in parts:
                    try:
                        page.wait_for_selector(sel, timeout=300)  # krótki check
                        found = True
                        break
                    except Exception:
                        continue
                if not found:
                    # finalnie normalny timeout dla pierwszego
                    page.wait_for_selector(parts[0])
            else:
                page.wait_for_selector(selector)

        elif action == "wait_for_url":
            if url is None:
                raise ValueError(f"Step 'wait_for_url' requires a non-None url in story '{story_name}'")
            page.wait_for_url(url)

        elif action == "wait_for_url_optional":
            # Nie blokujemy testu jeśli SPA nie robi twardej nawigacji.
            if url is None:
                raise ValueError(f"Step 'wait_for_url_optional' requires a non-None url in story '{story_name}'")
            try:
                page.wait_for_url(url, timeout=3000)
            except Exception:
                # brak twardej nawigacji — OK
                pass

        elif action == "expect":
            locator = page.locator(selector)
            if assertion == "visible":
                expect(locator).to_be_visible()
            elif assertion == "count":
                expect(locator).to_have_count(int(value))
            elif assertion == "contains_text":
                expect(locator).to_contain_text(value, timeout=5000)
            else:
                raise ValueError(f"Unknown assertion type: {assertion}")

        else:
            raise ValueError(f"Unknown action type: {action}")
