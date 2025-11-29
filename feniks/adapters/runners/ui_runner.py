# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
UI Scenario Runner - Executes browser UI scenarios and captures DOM snapshots.

Supports full browser automation with Playwright for legacy UI testing.
"""
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from feniks.core.models.behavior import (
    BehaviorScenario,
    BehaviorSnapshot,
    BehaviorViolation,
    DOMElement,
    ObservedDOM,
    ObservedLogs,
)
from feniks.exceptions import FeniksError
from feniks.infra.logging import get_logger

log = get_logger("adapters.runners.ui")

# Playwright import with graceful fallback
try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Page, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    log.warning("Playwright not installed. UI runner will not be functional.")


class UIRunner:
    """
    Executes UI behavior scenarios via Playwright browser automation.

    Features:
    - Full browser automation (Chromium, Firefox, WebKit)
    - DOM element capture with selectors
    - Screenshot capture
    - Console log monitoring
    - Network request tracking
    - User interaction simulation (click, type, navigate)
    - Wait conditions (element visible, network idle)
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        timeout: int = 30000,
        screenshot_on_failure: bool = True,
    ):
        """
        Initialize UI runner.

        Args:
            browser_type: Browser to use (chromium/firefox/webkit)
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
            screenshot_on_failure: Capture screenshot on failure
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise FeniksError("Playwright not installed. Install with: pip install playwright && playwright install")

        self.browser_type = browser_type
        self.headless = headless
        self.timeout = timeout
        self.screenshot_on_failure = screenshot_on_failure
        self.playwright = None
        self.browser = None

        log.info(f"UIRunner initialized (browser={browser_type}, headless={headless}, timeout={timeout}ms)")

    def __enter__(self):
        """Context manager entry - start browser."""
        self.playwright = sync_playwright().start()

        if self.browser_type == "chromium":
            self.browser = self.playwright.chromium.launch(headless=self.headless)
        elif self.browser_type == "firefox":
            self.browser = self.playwright.firefox.launch(headless=self.headless)
        elif self.browser_type == "webkit":
            self.browser = self.playwright.webkit.launch(headless=self.headless)
        else:
            raise FeniksError(f"Unsupported browser type: {self.browser_type}")

        log.debug(f"Browser launched: {self.browser_type}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser."""
        if self.browser:
            self.browser.close()
            log.debug("Browser closed")
        if self.playwright:
            self.playwright.stop()
            log.debug("Playwright stopped")

    def execute_scenario(self, scenario: BehaviorScenario, environment: str = "candidate") -> BehaviorSnapshot:
        """
        Execute a UI scenario and capture snapshot.

        Args:
            scenario: The behavior scenario to execute
            environment: Environment identifier (legacy/candidate/staging/production)

        Returns:
            BehaviorSnapshot with captured DOM state and validation results
        """
        if scenario.category not in ["ui", "mixed"]:
            raise FeniksError(f"UIRunner only supports 'ui' or 'mixed' scenarios, got: {scenario.category}")

        if not scenario.input.ui_actions:
            raise FeniksError("Scenario has no ui_actions defined")

        log.info(f"Executing UI scenario: {scenario.name} (id={scenario.id}, env={environment})")

        start_time = time.time()
        console_logs = []
        screenshot_path = None

        try:
            # Create browser context and page
            context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080}, user_agent=scenario.input.context.get("user_agent")
            )
            page = context.new_page()
            page.set_default_timeout(self.timeout)

            # Setup console log capturing
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

            # Execute UI actions
            for action in scenario.input.ui_actions:
                self._execute_action(page, action)

            duration_ms = int((time.time() - start_time) * 1000)

            # Capture DOM state
            observed_dom = self._capture_dom(page, scenario)

            # Validate against success criteria
            violations = []
            success = True

            if scenario.success_criteria.dom:
                dom_violations = self._validate_dom_criteria(observed_dom, scenario.success_criteria.dom)
                violations.extend(dom_violations)
                if dom_violations:
                    success = False

            # Create snapshot
            snapshot = BehaviorSnapshot(
                id=f"snap-{scenario.id}-{uuid.uuid4().hex[:8]}",
                scenario_id=scenario.id,
                project_id=scenario.project_id,
                environment=environment,
                observed_dom=observed_dom,
                observed_logs=ObservedLogs(lines=console_logs),
                duration_ms=duration_ms,
                success=success,
                violations=violations,
                created_at=datetime.now(),
                recorded_by="ui_runner",
            )

            # Capture screenshot if available
            if scenario.input.context.get("capture_screenshot", True):
                screenshot_path = self._capture_screenshot(page, snapshot.id)
                if screenshot_path:
                    snapshot.metadata = {"screenshot": screenshot_path}

            log.info(
                f"Scenario executed: {scenario.id} (success={success}, "
                f"duration={duration_ms}ms, dom_elements={len(observed_dom.elements)})"
            )

            # Cleanup
            context.close()
            return snapshot

        except PlaywrightError as e:
            log.error(f"Playwright error: {e}")

            # Capture screenshot on failure
            if self.screenshot_on_failure and "page" in locals():
                screenshot_path = self._capture_screenshot(page, f"error-{scenario.id}")

            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Playwright error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
                screenshot_path=screenshot_path,
            )

        except Exception as e:
            log.error(f"Unexpected error executing scenario: {e}", exc_info=True)
            return self._create_error_snapshot(
                scenario=scenario,
                environment=environment,
                error_message=f"Unexpected error: {str(e)}",
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def _execute_action(self, page: Page, action: dict) -> None:
        """Execute a single UI action."""
        action_type = action.get("type")

        log.debug(f"Executing action: {action_type}")

        if action_type == "navigate":
            page.goto(action["url"])
            page.wait_for_load_state("networkidle")

        elif action_type == "click":
            page.click(action["selector"])
            if action.get("wait_for_navigation"):
                page.wait_for_load_state("networkidle")

        elif action_type == "fill":
            page.fill(action["selector"], action["value"])

        elif action_type == "type":
            page.type(action["selector"], action["value"], delay=action.get("delay", 0))

        elif action_type == "select":
            page.select_option(action["selector"], action["value"])

        elif action_type == "wait":
            if action.get("selector"):
                page.wait_for_selector(action["selector"], state=action.get("state", "visible"))
            elif action.get("timeout"):
                page.wait_for_timeout(action["timeout"])

        elif action_type == "screenshot":
            path = action.get("path", f"screenshot-{uuid.uuid4().hex[:8]}.png")
            page.screenshot(path=path)

        else:
            log.warning(f"Unknown action type: {action_type}")

    def _capture_dom(self, page: Page, scenario: BehaviorScenario) -> ObservedDOM:
        """Capture DOM state."""
        elements = []

        # Get selectors from success criteria
        selectors = []
        if scenario.success_criteria.dom:
            selectors.extend(scenario.success_criteria.dom.must_exist_selectors)
            selectors.extend(scenario.success_criteria.dom.must_be_visible_selectors)

        # Add custom selectors from scenario context
        custom_selectors = scenario.input.context.get("capture_selectors", [])
        selectors.extend(custom_selectors)

        # Remove duplicates
        selectors = list(set(selectors))

        # Capture each selector
        for selector in selectors:
            try:
                element_handle = page.query_selector(selector)
                if element_handle:
                    element = DOMElement(
                        selector=selector,
                        tag_name=element_handle.evaluate("el => el.tagName"),
                        text_content=element_handle.text_content() or "",
                        is_visible=element_handle.is_visible(),
                        attributes=element_handle.evaluate(
                            "el => Array.from(el.attributes).reduce((acc, attr) => ({...acc, [attr.name]: attr.value}), {})"
                        ),
                    )
                    elements.append(element)
            except Exception as e:
                log.warning(f"Failed to capture element {selector}: {e}")

        return ObservedDOM(elements=elements)

    def _validate_dom_criteria(self, observed: ObservedDOM, criteria) -> List[BehaviorViolation]:
        """Validate observed DOM against criteria."""
        violations = []

        # Get observed selectors
        observed_selectors = {e.selector for e in observed.elements if e.selector}

        # Check required selectors
        for selector in criteria.must_exist_selectors:
            if selector not in observed_selectors:
                violations.append(
                    BehaviorViolation(
                        code="DOM_SELECTOR_MISSING",
                        message=f"Required DOM selector not found: {selector}",
                        severity="high",
                        details={"selector": selector},
                    )
                )

        # Check forbidden selectors
        for selector in criteria.must_not_exist_selectors:
            if selector in observed_selectors:
                violations.append(
                    BehaviorViolation(
                        code="DOM_SELECTOR_FORBIDDEN",
                        message=f"Forbidden DOM selector found: {selector}",
                        severity="medium",
                        details={"selector": selector},
                    )
                )

        # Check visibility
        visible_selectors = {e.selector for e in observed.elements if e.selector and e.is_visible}
        for selector in criteria.must_be_visible_selectors:
            if selector not in visible_selectors:
                violations.append(
                    BehaviorViolation(
                        code="DOM_ELEMENT_NOT_VISIBLE",
                        message=f"Required element not visible: {selector}",
                        severity="medium",
                        details={"selector": selector},
                    )
                )

        return violations

    def _capture_screenshot(self, page: Page, snapshot_id: str) -> Optional[str]:
        """Capture screenshot and return path."""
        try:
            screenshot_dir = Path("data/behavior/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshot_dir / f"{snapshot_id}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)

            log.debug(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            log.warning(f"Failed to capture screenshot: {e}")
            return None

    def _create_error_snapshot(
        self,
        scenario: BehaviorScenario,
        environment: str,
        error_message: str,
        duration_ms: int,
        screenshot_path: Optional[str] = None,
    ) -> BehaviorSnapshot:
        """Create snapshot for error scenarios."""
        metadata = {}
        if screenshot_path:
            metadata["screenshot"] = screenshot_path

        return BehaviorSnapshot(
            id=f"snap-{scenario.id}-error-{uuid.uuid4().hex[:8]}",
            scenario_id=scenario.id,
            project_id=scenario.project_id,
            environment=environment,
            observed_logs=ObservedLogs(lines=[error_message]),
            duration_ms=duration_ms,
            success=False,
            violations=[
                BehaviorViolation(code="EXECUTION_ERROR", message=error_message, severity="critical", details={})
            ],
            error_count=1,
            created_at=datetime.now(),
            recorded_by="ui_runner",
            metadata=metadata,
        )


# ============================================================================
# Factory Function
# ============================================================================


def create_ui_runner(
    browser_type: str = "chromium", headless: bool = True, timeout: int = 30000, screenshot_on_failure: bool = True
) -> UIRunner:
    """
    Create UI runner instance.

    Args:
        browser_type: Browser to use (chromium/firefox/webkit)
        headless: Run browser in headless mode
        timeout: Default timeout in milliseconds
        screenshot_on_failure: Capture screenshot on failure

    Returns:
        UIRunner instance
    """
    return UIRunner(
        browser_type=browser_type, headless=headless, timeout=timeout, screenshot_on_failure=screenshot_on_failure
    )
