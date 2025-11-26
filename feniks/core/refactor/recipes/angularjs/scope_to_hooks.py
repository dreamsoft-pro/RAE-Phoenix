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
from typing import List, Dict, Any, Optional, Set
import re
from dataclasses import dataclass
from enum import Enum

from feniks.core.refactor.recipe import (
    RefactorRecipe, RefactorPlan, RefactorResult, RefactorRisk, FileChange
)
from feniks.core.models.types import SystemModel, Module, Chunk
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
    uses_scope: bool
    uses_root_scope: bool
    scope_properties: Set[str]
    root_scope_properties: Set[str]
    watchers: List[WatcherMetadata]
    events: List[EventMetadata]
    complexity_score: int


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
        """
        Initialize the recipe.

        Args:
            config: Optional configuration
        """
        super().__init__()
        self.config = config or {}
        self.state_strategy = self.config.get("state_strategy", "useState")
        self.global_state_strategy = self.config.get("global_state_strategy", "context")

    @property
    def name(self) -> str:
        return "angularjs.scope-to-hooks"

    @property
    def description(self) -> str:
        return "Migrate AngularJS $scope/$rootScope/$watch to React hooks and Context API"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.HIGH

    def analyze(
        self,
        system_model: SystemModel,
        target: Optional[Dict[str, Any]] = None
    ) -> Optional[RefactorPlan]:
        """
        Analyze the system for scope usage patterns.

        Args:
            system_model: The system model
            target: Optional targeting information

        Returns:
            RefactorPlan or None
        """
        log.info(f"Analyzing for $scope/$rootScope usage: {system_model.project_id}")

        # Find scope usage
        scope_usage = self._analyze_scope_usage(system_model, target)

        if not scope_usage:
            log.info("No scope usage found")
            return None

        # Assess risks
        risks = self._assess_risks(scope_usage)
        risk_level = self._calculate_risk_level(scope_usage)

        # Collect global events
        global_events = self._collect_global_events(scope_usage)

        # Create refactoring plan
        plan = RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[],
            target_files=[],
            rationale=f"Migrate scope patterns to React hooks in {len(scope_usage)} locations",
            risks=risks,
            risk_level=risk_level,
            estimated_changes=len(scope_usage) + (1 if global_events else 0),
            validation_steps=[
                "Verify useState/useEffect syntax",
                "Check Context providers are set up",
                "Validate watcher conversions",
                "Test event system",
                "Review deep watch conversions"
            ],
            metadata={
                "scope_usage_count": len(scope_usage),
                "root_scope_count": sum(1 for u in scope_usage if u.uses_root_scope),
                "watcher_count": sum(len(u.watchers) for u in scope_usage),
                "event_count": sum(len(u.events) for u in scope_usage),
                "global_events": global_events,
                "state_strategy": self.state_strategy,
                "global_state_strategy": self.global_state_strategy
            }
        )

        log.info(f"Created refactoring plan for scope migration")
        return plan

    def execute(
        self,
        plan: RefactorPlan,
        chunks: List[Chunk],
        dry_run: bool = True
    ) -> RefactorResult:
        """
        Execute the scope migration.

        Args:
            plan: The refactoring plan
            chunks: Code chunks
            dry_run: If True, don't write files

        Returns:
            RefactorResult with migration artifacts
        """
        log.info(f"Executing scope migration (dry_run={dry_run})")

        result = RefactorResult(plan=plan, success=True)

        try:
            # Generate global context if needed
            if plan.metadata.get("global_events"):
                context_code = self._generate_global_context(plan)
                context_path = "contexts/GlobalContext.tsx"

                context_change = FileChange(
                    file_path=context_path,
                    original_content="",
                    modified_content=context_code,
                    change_type="create"
                )
                result.file_changes.append(context_change)

                log.info(f"Generated global context: {context_path}")

            # Generate event bus if needed
            if plan.metadata["event_count"] > 0:
                event_bus_code = self._generate_event_bus()
                event_bus_path = "hooks/useEventBus.ts"

                event_bus_change = FileChange(
                    file_path=event_bus_path,
                    original_content="",
                    modified_content=event_bus_code,
                    change_type="create"
                )
                result.file_changes.append(event_bus_change)

                log.info(f"Generated event bus hook: {event_bus_path}")

            # Generate migration guide
            guide_code = self._generate_migration_guide(plan)
            guide_path = "docs/SCOPE_MIGRATION_GUIDE.md"

            guide_change = FileChange(
                file_path=guide_path,
                original_content="",
                modified_content=guide_code,
                change_type="create"
            )
            result.file_changes.append(guide_change)

            log.info("Generated migration guide")

        except Exception as e:
            log.error(f"Error during execution: {e}", exc_info=True)
            result.success = False
            result.errors.append(str(e))

        return result

    def validate(self, result: RefactorResult) -> bool:
        """
        Validate the migration result.

        Args:
            result: The refactoring result

        Returns:
            bool: True if validation passed
        """
        log.info("Validating scope migration")

        validation_results = {}

        # Check all files were generated
        validation_results["context_generated"] = any(
            'Context' in fc.file_path for fc in result.file_changes
        )

        # Check syntax
        for file_change in result.file_changes:
            if file_change.file_path.endswith(('.tsx', '.ts')):
                syntax_valid = self._validate_syntax(file_change.modified_content)
                validation_results[f"syntax_{file_change.file_path}"] = syntax_valid

        result.validation_results = validation_results

        return all(validation_results.values())

    # Helper methods

    def _analyze_scope_usage(
        self,
        system_model: SystemModel,
        target: Optional[Dict[str, Any]]
    ) -> List[ScopeUsageMetadata]:
        """Analyze scope usage across the codebase."""
        usage_list = []

        for module_name, module in system_model.modules.items():
            for chunk in module.chunks:
                # Check if chunk uses $scope or $rootScope
                if '$scope' in chunk.content or '$rootScope' in chunk.content:
                    usage = self._extract_scope_usage(chunk)
                    if usage:
                        usage_list.append(usage)

        return usage_list

    def _extract_scope_usage(self, chunk: Chunk) -> Optional[ScopeUsageMetadata]:
        """Extract scope usage metadata from a chunk."""
        try:
            uses_scope = '$scope' in chunk.content
            uses_root_scope = '$rootScope' in chunk.content

            if not (uses_scope or uses_root_scope):
                return None

            # Extract properties
            scope_properties = self._extract_scope_properties(chunk.content, '$scope')
            root_scope_properties = self._extract_scope_properties(chunk.content, '$rootScope')

            # Extract watchers
            watchers = self._extract_watchers(chunk.content)

            # Extract events
            events = self._extract_events(chunk.content)

            # Calculate complexity
            complexity_score = (
                len(scope_properties) +
                len(root_scope_properties) * 2 +
                len(watchers) * 3 +
                len(events) * 2
            )

            return ScopeUsageMetadata(
                uses_scope=uses_scope,
                uses_root_scope=uses_root_scope,
                scope_properties=scope_properties,
                root_scope_properties=root_scope_properties,
                watchers=watchers,
                events=events,
                complexity_score=complexity_score
            )

        except Exception as e:
            log.error(f"Error extracting scope usage: {e}", exc_info=True)
            return None

    def _extract_scope_properties(self, content: str, scope_var: str) -> Set[str]:
        """Extract property names from scope."""
        properties = set()

        # Pattern: $scope.propertyName
        pattern = rf'{re.escape(scope_var)}\.(\w+)'

        for match in re.finditer(pattern, content):
            prop_name = match.group(1)
            # Filter out AngularJS built-in methods
            if not prop_name.startswith('$'):
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
            deep = match.group(3) == 'true' if match.group(3) else False

            watchers.append(WatcherMetadata(
                watch_type=WatchType.SIMPLE,
                expression=expression,
                callback=callback,
                deep=deep,
                source_location=match.group(0)
            ))

        # $watchCollection
        watch_coll_pattern = r'\$scope\.\$watchCollection\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^,\)]+)\)'

        for match in re.finditer(watch_coll_pattern, content):
            expression = match.group(1)
            callback = match.group(2).strip()

            watchers.append(WatcherMetadata(
                watch_type=WatchType.COLLECTION,
                expression=expression,
                callback=callback,
                deep=False,
                source_location=match.group(0)
            ))

        return watchers

    def _extract_events(self, content: str) -> List[EventMetadata]:
        """Extract event definitions."""
        events = []

        # $on pattern
        on_pattern = r'\$(?:scope|rootScope)\.\$on\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^\)]+)\)'

        for match in re.finditer(on_pattern, content):
            event_name = match.group(1)
            handler = match.group(2).strip()

            events.append(EventMetadata(
                event_type=EventType.ON,
                event_name=event_name,
                handler_or_data=handler,
                source_location=match.group(0)
            ))

        # $broadcast pattern
        broadcast_pattern = r'\$(?:scope|rootScope)\.\$broadcast\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*([^\)]+))?\)'

        for match in re.finditer(broadcast_pattern, content):
            event_name = match.group(1)
            data = match.group(2).strip() if match.group(2) else None

            events.append(EventMetadata(
                event_type=EventType.BROADCAST,
                event_name=event_name,
                handler_or_data=data or "{}",
                source_location=match.group(0)
            ))

        # $emit pattern
        emit_pattern = r'\$(?:scope|rootScope)\.\$emit\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*([^\)]+))?\)'

        for match in re.finditer(emit_pattern, content):
            event_name = match.group(1)
            data = match.group(2).strip() if match.group(2) else None

            events.append(EventMetadata(
                event_type=EventType.EMIT,
                event_name=event_name,
                handler_or_data=data or "{}",
                source_location=match.group(0)
            ))

        return events

    def _assess_risks(self, usage_list: List[ScopeUsageMetadata]) -> List[str]:
        """Assess risks for scope migration."""
        risks = []

        # Check for high complexity
        high_complexity = [u for u in usage_list if u.complexity_score > 20]
        if high_complexity:
            risks.append(f"{len(high_complexity)} locations have high complexity scores")

        # Check for deep watchers
        deep_watchers = sum(
            sum(1 for w in u.watchers if w.deep)
            for u in usage_list
        )
        if deep_watchers > 0:
            risks.append(f"{deep_watchers} deep watchers require careful conversion")

        # Check for $rootScope usage
        root_scope_count = sum(1 for u in usage_list if u.uses_root_scope)
        if root_scope_count > 0:
            risks.append(f"{root_scope_count} locations use $rootScope (global state)")

        # Check for event bus patterns
        event_count = sum(len(u.events) for u in usage_list)
        if event_count > 10:
            risks.append(f"{event_count} scope events detected (may need event bus refactor)")

        risks.extend([
            "Watcher callbacks may have side effects that need review",
            "Event timing may differ between AngularJS and React",
            "Deep watches are expensive - consider alternative patterns",
            "$rootScope patterns need careful global state design"
        ])

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

        events_interface = '\n  '.join([f'{event}: any;' for event in events])

        context = f"""// Generated by Feniks - Global Context for $rootScope replacement
// TODO: Review and adjust state structure
// TODO: Implement proper TypeScript types

import React, {{ createContext, useContext, useState, useCallback, ReactNode }} from 'react';

interface GlobalState {{
  // TODO: Add global state properties from $rootScope
  [key: string]: any;
}}

interface GlobalEvents {{
  {events_interface}
}}

interface GlobalContextType {{
  state: GlobalState;
  setState: (updates: Partial<GlobalState>) => void;
  on: (eventName: string, handler: (data: any) => void) => () => void;
  emit: (eventName: string, data?: any) => void;
}}

const GlobalContext = createContext<GlobalContextType | undefined>(undefined);

export function GlobalProvider({{ children }}: {{ children: ReactNode }}) {{
  const [state, setStateInternal] = useState<GlobalState>({{}});
  const [listeners, setListeners] = useState<Map<string, Set<(data: any) => void>>>(new Map());

  const setState = useCallback((updates: Partial<GlobalState>) => {{
    setStateInternal(prev => ({{ ...prev, ...updates }}));
  }}, []);

  const on = useCallback((eventName: string, handler: (data: any) => void) => {{
    setListeners(prev => {{
      const newListeners = new Map(prev);
      if (!newListeners.has(eventName)) {{
        newListeners.set(eventName, new Set());
      }}
      newListeners.get(eventName)!.add(handler);
      return newListeners;
    }});

    // Return unsubscribe function
    return () => {{
      setListeners(prev => {{
        const newListeners = new Map(prev);
        const eventListeners = newListeners.get(eventName);
        if (eventListeners) {{
          eventListeners.delete(handler);
          if (eventListeners.size === 0) {{
            newListeners.delete(eventName);
          }}
        }}
        return newListeners;
      }});
    }};
  }}, []);

  const emit = useCallback((eventName: string, data?: any) => {{
    const eventListeners = listeners.get(eventName);
    if (eventListeners) {{
      eventListeners.forEach(handler => handler(data));
    }}
  }}, [listeners]);

  const value = {{
    state,
    setState,
    on,
    emit
  }};

  return (
    <GlobalContext.Provider value={{value}}>
      {{children}}
    </GlobalContext.Provider>
  );
}}

export function useGlobal() {{
  const context = useContext(GlobalContext);
  if (!context) {{
    throw new Error('useGlobal must be used within GlobalProvider');
  }}
  return context;
}}

// Convenience hooks for specific events
{self._generate_event_hooks(events)}
"""

        return context

    def _generate_event_hooks(self, events: List[str]) -> str:
        """Generate convenience hooks for events."""
        hooks = []

        for event in events:
            hook_name = f"use{self._to_camel_case(event)}Event"
            hooks.append(f"""
export function {hook_name}(handler: (data: any) => void) {{
  const {{ on }} = useGlobal();

  React.useEffect(() => {{
    return on('{event}', handler);
  }}, [handler, on]);
}}""")

        return '\n'.join(hooks)

    def _to_camel_case(self, text: str) -> str:
        """Convert text to CamelCase."""
        parts = re.split(r'[-_:]', text)
        return ''.join(word.capitalize() for word in parts)

    def _generate_event_bus(self) -> str:
        """Generate event bus hook."""
        return """// Generated by Feniks - Event Bus Hook
// Alternative to global context for event communication

import { useEffect, useCallback, useRef } from 'react';

type EventHandler = (data: any) => void;

class EventBus {
  private listeners: Map<string, Set<EventHandler>> = new Map();

  on(eventName: string, handler: EventHandler): () => void {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set());
    }
    this.listeners.get(eventName)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.listeners.get(eventName);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.listeners.delete(eventName);
        }
      }
    };
  }

  emit(eventName: string, data?: any): void {
    const handlers = this.listeners.get(eventName);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  off(eventName: string, handler?: EventHandler): void {
    if (!handler) {
      this.listeners.delete(eventName);
      return;
    }

    const handlers = this.listeners.get(eventName);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.listeners.delete(eventName);
      }
    }
  }
}

const eventBus = new EventBus();

export function useEventBus() {
  return eventBus;
}

export function useEventListener(eventName: string, handler: EventHandler) {
  const handlerRef = useRef(handler);

  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    const wrappedHandler = (data: any) => handlerRef.current(data);
    return eventBus.on(eventName, wrappedHandler);
  }, [eventName]);
}
"""

    def _generate_migration_guide(self, plan: RefactorPlan) -> str:
        """Generate migration guide document."""
        return f"""# Scope Migration Guide

Generated by Feniks - AngularJS to React Migration

## Overview

This guide helps migrate AngularJS `$scope`, `$rootScope`, and `$watch` patterns to React hooks.

## Statistics

- **Scope usage locations**: {plan.metadata['scope_usage_count']}
- **$rootScope usage**: {plan.metadata['root_scope_count']}
- **Watchers**: {plan.metadata['watcher_count']}
- **Events**: {plan.metadata['event_count']}

## Migration Patterns

### 1. $scope → useState

**Before (AngularJS):**
```javascript
$scope.name = 'John';
$scope.age = 30;

$scope.updateName = function(newName) {{
  $scope.name = newName;
}};
```

**After (React):**
```typescript
const [name, setName] = useState('John');
const [age, setAge] = useState(30);

const updateName = (newName: string) => {{
  setName(newName);
}};
```

### 2. $watch → useEffect

**Before (AngularJS):**
```javascript
$scope.$watch('vm.value', function(newVal, oldVal) {{
  console.log('Value changed:', newVal);
}});
```

**After (React):**
```typescript
useEffect(() => {{
  console.log('Value changed:', value);
}}, [value]);
```

### 3. Deep $watch → useEffect with JSON.stringify

**Before (AngularJS):**
```javascript
$scope.$watch('vm.obj', function(newVal, oldVal) {{
  // Handle change
}}, true); // deep watch
```

**After (React):**
```typescript
const objString = JSON.stringify(obj);
useEffect(() => {{
  // Handle change
}}, [objString]);

// Or use a deep comparison library like use-deep-compare-effect
```

### 4. $rootScope → Context API

**Before (AngularJS):**
```javascript
$rootScope.user = {{ id: 1, name: 'John' }};

// In another controller
$scope.$watch(function() {{
  return $rootScope.user;
}}, function(user) {{
  console.log('User changed:', user);
}});
```

**After (React):**
```typescript
// In GlobalProvider
const {{ state, setState }} = useGlobal();

// Set user
setState({{ user: {{ id: 1, name: 'John' }} }});

// Watch user
useEffect(() => {{
  console.log('User changed:', state.user);
}}, [state.user]);
```

### 5. $scope events → Custom events

**Before (AngularJS):**
```javascript
// Emit event
$rootScope.$broadcast('user:login', {{ userId: 123 }});

// Listen to event
$scope.$on('user:login', function(event, data) {{
  console.log('User logged in:', data.userId);
}});
```

**After (React):**
```typescript
// Emit event
const {{ emit }} = useGlobal();
emit('user:login', {{ userId: 123 }});

// Listen to event
const {{ on }} = useGlobal();
useEffect(() => {{
  return on('user:login', (data) => {{
    console.log('User logged in:', data.userId);
  }});
}}, [on]);

// Or use the convenience hook
useUserLoginEvent((data) => {{
  console.log('User logged in:', data.userId);
}});
```

## Global Events

The following global events were detected in your codebase:

{self._format_event_list(plan.metadata.get('global_events', []))}

## Best Practices

1. **Avoid over-using global state**: Prefer component-local state when possible
2. **Use Context sparingly**: Too many contexts can hurt performance
3. **Memoize callbacks**: Use `useCallback` for event handlers
4. **Clean up effects**: Always return cleanup functions from `useEffect`
5. **Consider libraries**: For complex state, consider Zustand, Jotai, or Redux

## Next Steps

1. Review generated Context providers
2. Update components to use hooks instead of $scope
3. Test watcher conversions carefully
4. Migrate event listeners to new system
5. Remove AngularJS dependencies

## Risk Areas

{self._format_risk_list(plan.risks)}

---

Generated on: {plan.metadata.get('timestamp', 'N/A')}
"""

    def _format_event_list(self, events: List[str]) -> str:
        """Format event list for markdown."""
        if not events:
            return "- None detected"
        return '\n'.join([f"- `{event}`" for event in events])

    def _format_risk_list(self, risks: List[str]) -> str:
        """Format risk list for markdown."""
        return '\n'.join([f"- {risk}" for risk in risks])

    def _validate_syntax(self, content: str) -> bool:
        """Basic syntax validation."""
        if content.count('{') != content.count('}'):
            return False
        if content.count('(') != content.count(')'):
            return False

        return True
