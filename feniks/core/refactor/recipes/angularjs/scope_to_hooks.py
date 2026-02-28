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
Scope to Hooks Recipe - Migrates AngularJS $scope/$rootScope/$watch to React hooks.

Handles:
- $scope → useState/useReducer in components
- $rootScope → Context API or global store
- $watch → useEffect with dependencies
- $watchCollection → useEffect with array dependencies
- $watchGroup → useEffect with multiple dependencies
- $scope.$on → Event bus or Context-based events
- $scope.$broadcast/$emit → Context-based events
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.scope_to_hooks")


class WatchType(Enum):
    """Types of watchers."""

    SIMPLE = "$watch"
    COLLECTION = "$watchCollection"
    GROUP = "$watchGroup"


class EventType(Enum):
    """Types of scope events."""

    ON = "$on"
    BROADCAST = "$broadcast"
    EMIT = "$emit"


@dataclass
class WatcherMetadata:
    """Metadata for a watcher."""

    watch_type: WatchType
    expression: str
    callback: str
    deep: bool
    source_location: str


@dataclass
class EventMetadata:
    """Metadata for a scope event."""

    event_type: EventType
    event_name: str
    handler_or_data: str
    source_location: str


@dataclass
class ScopeUsageMetadata:
    """Metadata about $scope/$rootScope usage."""

    source_file: str
    uses_scope: bool
    uses_root_scope: bool
    scope_properties: Set[str]
    root_scope_properties: Set[str]
    watchers: List[WatcherMetadata]
    events: List[EventMetadata]
    complexity_score: int

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "source_file": self.source_file,
            "uses_scope": self.uses_scope,
            "uses_root_scope": self.uses_root_scope,
            "scope_properties": list(self.scope_properties),
            "root_scope_properties": list(self.root_scope_properties),
            "watchers": [
                {
                    "watch_type": w.watch_type.value,
                    "expression": w.expression,
                    "callback": w.callback,
                    "deep": w.deep,
                    "source_location": w.source_location,
                }
                for w in self.watchers
            ],
            "events": [
                {
                    "event_type": e.event_type.value,
                    "event_name": e.event_name,
                    "handler_or_data": e.handler_or_data,
                    "source_location": e.source_location,
                }
                for e in self.events
            ],
            "complexity_score": self.complexity_score,
        }


class ScopeToHooksRecipe(RefactorRecipe):
    """
    Recipe for migrating AngularJS scope patterns to React hooks.

    Mapping strategy:
    - $scope local state → useState/useReducer
    - $rootScope shared state → Context API
    - $watch(expr, callback) → useEffect(() => callback(), [expr])
    - $watchCollection(arr, cb) → useEffect(() => cb(), [arr])
    - $scope.$on(event, handler) → Context-based event system
    - $broadcast/$emit → Context-based pub-sub
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.state_strategy = self.config.get("state_strategy", "useState")
        self.global_state_strategy = self.config.get("global_state_strategy", "context")
        self.target_hooks_dir = self.config.get("target_hooks_dir", "hooks/legacy")

    @property
    def name(self) -> str:
        return "angularjs.scope-to-hooks"

    @property
    def description(self) -> str:
        return "Migrate AngularJS $scope/$rootScope/$watch to React hooks and Context API"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.HIGH

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        log.info(f"Analyzing for $scope/$rootScope usage: {system_model.project_id}")

        scope_usage = self._analyze_scope_usage(system_model, target)

        if not scope_usage:
            log.info("No scope usage found")
            return None

        risks = self._assess_risks(scope_usage)
        risk_level = self._calculate_risk_level(scope_usage)
        global_events = self._collect_global_events(scope_usage)

        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[],
            target_files=[u.source_file for u in scope_usage],
            rationale=f"Migrate scope patterns to React hooks in {len(scope_usage)} locations",
            risks=risks,
            risk_level=risk_level,
            estimated_changes=len(scope_usage) * 2 + (1 if global_events else 0),
            validation_steps=[
                "Verify useState/useEffect syntax",
                "Check Context providers are set up",
                "Validate watcher conversions",
                "Test event system",
                "Review deep watch conversions",
            ],
            metadata={
                "scope_usages": [u.to_dict() for u in scope_usage],
                "scope_usage_count": len(scope_usage),
                "root_scope_count": sum(1 for u in scope_usage if u.uses_root_scope),
                "watcher_count": sum(len(u.watchers) for u in scope_usage),
                "event_count": sum(len(u.events) for u in scope_usage),
                "global_events": global_events,
                "state_strategy": self.state_strategy,
                "global_state_strategy": self.global_state_strategy,
                "target_hooks_dir": self.target_hooks_dir,
            },
        )

        log.info("Created refactoring plan for scope migration")
        return plan

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        log.info(f"Executing scope migration (dry_run={dry_run})")
        result = RefactorResult(plan=plan, success=True)

        try:
            # 1. Generate Global Context if needed
            if plan.metadata.get("global_events") or plan.metadata.get("root_scope_count", 0) > 0:
                context_code = self._generate_global_context(plan)
                context_path = "contexts/GlobalContext.tsx"
                result.file_changes.append(
                    FileChange(
                        file_path=context_path, original_content="", modified_content=context_code, change_type="create"
                    )
                )
                log.info(f"Generated global context: {context_path}")

            # 2. Generate Event Bus if needed
            if plan.metadata["event_count"] > 0:
                event_bus_code = self._generate_event_bus()
                event_bus_path = "hooks/useEventBus.ts"
                result.file_changes.append(
                    FileChange(
                        file_path=event_bus_path,
                        original_content="",
                        modified_content=event_bus_code,
                        change_type="create",
                    )
                )
                log.info(f"Generated event bus hook: {event_bus_path}")

            # 3. Generate Specific Hooks for each Scope
            target_dir = plan.metadata.get("target_hooks_dir", "hooks/legacy")
            for usage_dict in plan.metadata.get("scope_usages", []):
                hook_code = self._generate_scope_hook(usage_dict)

                # Determine hook name from source file
                source_file = usage_dict["source_file"]
                # e.g., apps/legacy/controllers/LoginCtrl.js -> useLoginCtrlScope.ts
                base_name = source_file.split("/")[-1].split(".")[0]
                base_name = re.sub(r"[-_]", "", base_name)  # simple sanitization
                hook_name = f"use{base_name.capitalize()}Scope"

                hook_path = f"{target_dir}/{hook_name}.ts"

                result.file_changes.append(
                    FileChange(
                        file_path=hook_path, original_content="", modified_content=hook_code, change_type="create"
                    )
                )
                log.info(f"Generated scope hook: {hook_path}")

            # 4. Generate Migration Guide
            guide_code = self._generate_migration_guide(plan)
            guide_path = "docs/SCOPE_MIGRATION_GUIDE.md"
            result.file_changes.append(
                FileChange(file_path=guide_path, original_content="", modified_content=guide_code, change_type="create")
            )
            log.info("Generated migration guide")

        except Exception as e:
            log.error(f"Error during execution: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        return result

    def validate(self, result: RefactorResult) -> bool:
        """Validate the migration result."""
        log.info("Validating scope migration")
        validation_results = {}
        validation_results["context_generated"] = any("Context" in fc.file_path for fc in result.file_changes)
        result.validation_results = validation_results
        return all(validation_results.values())

    # Helper methods

    def _analyze_scope_usage(
        self, system_model: SystemModel, target: Optional[Dict[str, Any]]
    ) -> List[ScopeUsageMetadata]:
        """Analyze scope usage across the codebase."""
        usage_list = []

        for module_name, module in system_model.modules.items():
            for chunk in module.chunks:
                # Check if chunk uses $scope or $rootScope
                if "$scope" in chunk.content or "$rootScope" in chunk.content:
                    usage = self._extract_scope_usage(chunk)
                    if usage:
                        usage_list.append(usage)

        return usage_list

    def _extract_scope_usage(self, chunk: Chunk) -> Optional[ScopeUsageMetadata]:
        """Extract scope usage metadata from a chunk."""
        try:
            uses_scope = "$scope" in chunk.content
            uses_root_scope = "$rootScope" in chunk.content

            if not (uses_scope or uses_root_scope):
                return None

            # Extract properties
            scope_properties = self._extract_scope_properties(chunk.content, "$scope")
            root_scope_properties = self._extract_scope_properties(chunk.content, "$rootScope")

            # Extract watchers
            watchers = self._extract_watchers(chunk.content)

            # Extract events
            events = self._extract_events(chunk.content)

            # Calculate complexity
            complexity_score = (
                len(scope_properties) + len(root_scope_properties) * 2 + len(watchers) * 3 + len(events) * 2
            )

            return ScopeUsageMetadata(
                source_file=chunk.file_path,
                uses_scope=uses_scope,
                uses_root_scope=uses_root_scope,
                scope_properties=scope_properties,
                root_scope_properties=root_scope_properties,
                watchers=watchers,
                events=events,
                complexity_score=complexity_score,
            )

        except Exception as e:
            log.error(f"Error extracting scope usage: {e}", exc_info=True)
            return None

    def _extract_scope_properties(self, content: str, scope_var: str) -> Set[str]:
        """Extract property names from scope."""
        properties = set()

        # Pattern: $scope.propertyName
        pattern = rf"{re.escape(scope_var)}\.(\w+)"

        for match in re.finditer(pattern, content):
            prop_name = match.group(1)
            # Filter out AngularJS built-in methods
            if not prop_name.startswith("$"):
                properties.add(prop_name)

        return properties

    def _extract_watchers(self, content: str) -> List[WatcherMetadata]:
        """Extract watcher definitions."""
        watchers = []

        # $watch patterns
        watch_pattern = r'\$scope\.\$watch\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^,\)]+)(?:,\s*(true|false))?\)'

        for match in re.finditer(watch_pattern, content):
            expression = match.group(1)
            callback = match.group(2).strip()
            deep = match.group(3) == "true" if match.group(3) else False

            watchers.append(
                WatcherMetadata(
                    watch_type=WatchType.SIMPLE,
                    expression=expression,
                    callback=callback,
                    deep=deep,
                    source_location=match.group(0),
                )
            )

        # $watchCollection
        watch_coll_pattern = r'\$scope\.\$watchCollection\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^,\)]+)\)'

        for match in re.finditer(watch_coll_pattern, content):
            expression = match.group(1)
            callback = match.group(2).strip()

            watchers.append(
                WatcherMetadata(
                    watch_type=WatchType.COLLECTION,
                    expression=expression,
                    callback=callback,
                    deep=False,
                    source_location=match.group(0),
                )
            )

        return watchers

    def _extract_events(self, content: str) -> List[EventMetadata]:
        """Extract event definitions."""
        events = []

        # $on pattern
        on_pattern = r'\$(?:scope|rootScope)\.\$on\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^\)]+)\)'

        for match in re.finditer(on_pattern, content):
            event_name = match.group(1)
            handler = match.group(2).strip()

            events.append(
                EventMetadata(
                    event_type=EventType.ON,
                    event_name=event_name,
                    handler_or_data=handler,
                    source_location=match.group(0),
                )
            )

        # $broadcast pattern
        broadcast_pattern = r'\$(?:scope|rootScope)\.\$broadcast\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*([^\)]+))?\)'

        for match in re.finditer(broadcast_pattern, content):
            event_name = match.group(1)
            data = match.group(2).strip() if match.group(2) else None

            events.append(
                EventMetadata(
                    event_type=EventType.BROADCAST,
                    event_name=event_name,
                    handler_or_data=data or "{}",
                    source_location=match.group(0),
                )
            )

        # $emit pattern
        emit_pattern = r'\$(?:scope|rootScope)\.\$emit\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*([^\)]+))?\)'

        for match in re.finditer(emit_pattern, content):
            event_name = match.group(1)
            data = match.group(2).strip() if match.group(2) else None

            events.append(
                EventMetadata(
                    event_type=EventType.EMIT,
                    event_name=event_name,
                    handler_or_data=data or "{}",
                    source_location=match.group(0),
                )
            )

        return events

    def _assess_risks(self, usage_list: List[ScopeUsageMetadata]) -> List[str]:
        """Assess risks for scope migration."""
        risks = []

        # Check for high complexity
        high_complexity = [u for u in usage_list if u.complexity_score > 20]
        if high_complexity:
            risks.append(f"{len(high_complexity)} locations have high complexity scores")

        # Check for deep watchers
        deep_watchers = sum(sum(1 for w in u.watchers if w.deep) for u in usage_list)
        if deep_watchers > 0:
            risks.append(f"{deep_watchers} deep watchers require careful conversion")

        # Check for $rootScope usage
        root_scope_count = sum(1 for u in usage_list if u.uses_root_scope)
        if root_scope_count > 0:
            risks.append(f"{root_scope_count} locations use $rootScope (global state)")

        return risks

    def _calculate_risk_level(self, usage_list: List[ScopeUsageMetadata]) -> RefactorRisk:
        """Calculate overall risk level."""
        if not usage_list:
            return RefactorRisk.LOW

        avg_complexity = sum(u.complexity_score for u in usage_list) / len(usage_list)
        root_scope_usage = sum(1 for u in usage_list if u.uses_root_scope)

        if avg_complexity > 20 or root_scope_usage > len(usage_list) / 3:
            return RefactorRisk.HIGH
        elif avg_complexity > 10 or root_scope_usage > 0:
            return RefactorRisk.MEDIUM
        else:
            return RefactorRisk.LOW

    def _collect_global_events(self, usage_list: List[ScopeUsageMetadata]) -> List[str]:
        """Collect all global event names."""
        events = set()

        for usage in usage_list:
            for event in usage.events:
                events.add(event.event_name)

        return sorted(list(events))

    def _generate_global_context(self, plan: RefactorPlan) -> str:
        """Generate global context for $rootScope replacement."""
        events = plan.metadata.get("global_events", [])
        events_interface = "\n  ".join([f"{event}: any;" for event in events])

        return f"""
// Generated by Feniks - Global Context
import React, {{ createContext, useContext, useState, useCallback, ReactNode }} from 'react';

interface GlobalState {{
  [key: string]: any;
}}

interface GlobalEvents {{
  {events_interface}
}}

const GlobalContext = createContext<any>(null);

export function GlobalProvider({{ children }}: {{ children: ReactNode }}) {{
  const [state, setState] = useState<GlobalState>({{}});

  const on = useCallback((eventName: string, handler: (data: any) => void) => {{
    // TODO: Implement event listener logic
    return () => {{}};
  }}, []);

  const emit = useCallback((eventName: string, data?: any) => {{
    // TODO: Implement event emit logic
  }}, []);

  return (
    <GlobalContext.Provider value={{{{ state, setState, on, emit }}}}
    >
      {{children}}
    </GlobalContext.Provider>
  );
}}

export function useGlobal() {{
  return useContext(GlobalContext);
}}
"""

    def _generate_event_bus(self) -> str:
        """Generate event bus hook."""
        return """// Generated by Feniks - Event Bus Hook
import { useEffect, useState } from 'react';

export function useEventBus() {
  // Simple event bus stub
  return {
    on: (event: string, handler: any) => {},
    emit: (event: string, data: any) => {}
  };
}
"""

    def _generate_scope_hook(self, usage: Dict[str, Any]) -> str:
        """Generate a custom React hook encapsulating the legacy scope logic."""
        source_file = usage["source_file"]
        props = usage["scope_properties"]
        watchers = usage["watchers"]

        lines = [
            f"// Generated by Feniks - Scope Hook for {source_file}",
            "import { useState, useEffect } from 'react';",
            "import { useGlobal } from '@/contexts/GlobalContext';",
            "",
            "export function useLegacyScope() {",
            "  const { state: globalState, setState: setGlobalState } = useGlobal();",
        ]

        # Generate State
        for prop in props:
            lines.append("  const [{prop}, set{prop.capitalize()}] = useState<any>(null);")

        lines.append("")

        # Generate Watchers (Effects)
        for i, watch in enumerate(watchers):
            expr = watch["expression"]
            # Heuristic: if expression looks like a property, use it as dependency
            dep = expr if expr in props else ""
            lines.append(f"  // Watcher {i+1}: {expr}")
            lines.append("  useEffect(() => {")
            lines.append(f"    // Original callback: {watch['callback']}")
            lines.append("    // TODO: Implement watcher logic")
            lines.append(f"  }}, [{dep}]);")
            lines.append("")

        # Return values
        lines.append("  return {")
        for prop in props:
            lines.append("    {prop}, set{prop.capitalize()},")
        lines.append("    globalState,")
        lines.append("    setGlobalState")
        lines.append("  };")
        lines.append("}")

        return "\n".join(lines)

    def _generate_migration_guide(self, plan: RefactorPlan) -> str:
        """Generate migration guide document."""
        return f"""# Scope Migration Guide

Generated by Feniks - AngularJS to React Migration

## Overview

This guide helps migrate AngularJS `$scope`, `$rootScope`, and `$watch` patterns to React hooks.

- **Scope usage locations**: {plan.metadata['scope_usage_count']}
- **$rootScope usage**: {plan.metadata['root_scope_count']}
- **Watchers**: {plan.metadata['watcher_count']}

See `hooks/legacy/` for generated hooks for each controller.
"""
