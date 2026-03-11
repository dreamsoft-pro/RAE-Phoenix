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
Capability Detector - detects system capabilities from code patterns.
Analyzes chunks, modules, and dependencies to infer what the system can do.
"""
import re
from collections import defaultdict
from typing import Dict, List

from feniks.core.models.types import Capability, Chunk, SystemModel
from feniks.infra.logging import get_logger

log = get_logger("core.capability_detector")


class CapabilityDetector:
    """Detects system capabilities from code analysis."""

    def __init__(self):
        """Initialize the capability detector."""
        self.capability_patterns = self._build_capability_patterns()

    def _build_capability_patterns(self) -> Dict[str, Dict]:
        """
        Build patterns for detecting capabilities.

        Returns:
            Dict mapping capability name to detection patterns
        """
        return {
            "http_client": {
                "description": "HTTP client for external API calls",
                "type": "integration",
                "patterns": [r"\$http", r"fetch\(", r"axios", r"XMLHttpRequest"],
                "business_domain": "integration",
            },
            "routing": {
                "description": "UI routing and navigation",
                "type": "feature",
                "patterns": [r"\$route", r"ui-router", r"ngRoute", r"Router"],
                "business_domain": "navigation",
            },
            "authentication": {
                "description": "User authentication and authorization",
                "type": "feature",
                "patterns": [r"auth", r"login", r"logout", r"session", r"token", r"jwt"],
                "business_domain": "security",
            },
            "data_binding": {
                "description": "Two-way data binding",
                "type": "pattern",
                "patterns": [r"ng-model", r"ng-bind", r"\$scope\.\$watch"],
                "business_domain": "ui",
            },
            "form_handling": {
                "description": "Form validation and handling",
                "type": "feature",
                "patterns": [r"ng-form", r"form\s+validation", r"\$valid", r"\$invalid"],
                "business_domain": "ui",
            },
            "state_management": {
                "description": "Application state management",
                "type": "pattern",
                "patterns": [r"redux", r"vuex", r"ngrx", r"store", r"\$rootScope"],
                "business_domain": "architecture",
            },
            "rest_api": {
                "description": "RESTful API endpoints",
                "type": "integration",
                "patterns": [r"\/api\/", r"REST", r"endpoint"],
                "business_domain": "integration",
            },
            "payment": {
                "description": "Payment processing",
                "type": "feature",
                "patterns": [r"payment", r"checkout", r"transaction", r"billing", r"stripe", r"paypal"],
                "business_domain": "payment",
            },
            "analytics": {
                "description": "Analytics and reporting",
                "type": "feature",
                "patterns": [r"analytics", r"tracking", r"metric", r"report", r"dashboard"],
                "business_domain": "analytics",
            },
            "notification": {
                "description": "User notifications",
                "type": "feature",
                "patterns": [r"notification", r"alert", r"toast", r"message"],
                "business_domain": "ui",
            },
            "localization": {
                "description": "Internationalization and localization",
                "type": "feature",
                "patterns": [r"i18n", r"translate", r"locale", r"language"],
                "business_domain": "localization",
            },
            "websocket": {
                "description": "Real-time communication via WebSocket",
                "type": "integration",
                "patterns": [r"WebSocket", r"socket\.io", r"ws://"],
                "business_domain": "realtime",
            },
            "file_upload": {
                "description": "File upload functionality",
                "type": "feature",
                "patterns": [r"upload", r"file\s+select", r"FormData", r"multipart"],
                "business_domain": "file",
            },
            "caching": {
                "description": "Data caching",
                "type": "pattern",
                "patterns": [r"cache", r"\$cacheFactory", r"localStorage", r"sessionStorage"],
                "business_domain": "performance",
            },
        }

    def detect_from_chunks(self, chunks: List[Chunk]) -> List[Capability]:
        """
        Detect capabilities from code chunks.

        Args:
            chunks: List of code chunks to analyze

        Returns:
            List of detected capabilities
        """
        log.info("Detecting capabilities from chunks...")

        detected_capabilities: Dict[str, Dict] = defaultdict(
            lambda: {"chunks": [], "modules": set(), "patterns": set(), "confidence": 0.0}
        )

        # Analyze each chunk
        for chunk in chunks:
            chunk_text = chunk.text.lower()
            module_name = chunk.module or "unknown"

            # Check each capability pattern
            for cap_name, cap_config in self.capability_patterns.items():
                patterns = cap_config["patterns"]
                matches = []

                for pattern in patterns:
                    if re.search(pattern, chunk_text, re.IGNORECASE):
                        matches.append(pattern)

                # If we found matches, record the capability
                if matches:
                    detected_capabilities[cap_name]["chunks"].append(chunk.id)
                    detected_capabilities[cap_name]["modules"].add(module_name)
                    detected_capabilities[cap_name]["patterns"].update(matches)
                    detected_capabilities[cap_name]["confidence"] += 0.1

        # Convert to Capability objects
        capabilities = []
        for cap_name, data in detected_capabilities.items():
            config = self.capability_patterns[cap_name]

            # Normalize confidence
            confidence = min(data["confidence"], 1.0)

            # Calculate complexity score (based on number of modules involved)
            complexity_score = len(data["modules"]) / 10.0

            capability = Capability(
                name=cap_name,
                description=config["description"],
                capability_type=config["type"],
                confidence=confidence,
                modules=list(data["modules"]),
                chunks=data["chunks"],
                patterns=list(data["patterns"]),
                business_domain=config["business_domain"],
                complexity_score=complexity_score,
            )
            capabilities.append(capability)

        log.info(f"Detected {len(capabilities)} capabilities")

        return capabilities

    def detect_from_system_model(self, system_model: SystemModel) -> List[Capability]:
        """
        Detect additional capabilities from system model analysis.

        Args:
            system_model: The system model

        Returns:
            List of additional capabilities
        """
        log.info("Detecting capabilities from system model...")

        capabilities = []

        # Detect module structure capabilities
        if len(system_model.modules) > 10:
            capabilities.append(
                Capability(
                    name="modular_architecture",
                    description="Well-structured modular architecture",
                    capability_type="pattern",
                    confidence=0.8,
                    modules=list(system_model.modules.keys())[:5],
                    patterns=["multiple_modules"],
                    business_domain="architecture",
                    complexity_score=len(system_model.modules) / 20.0,
                )
            )

        # Detect API capability from endpoints
        if len(system_model.api_endpoints) > 5:
            modules_with_api = set()
            for module in system_model.modules.values():
                if any(endpoint for chunk in module.chunks for endpoint in system_model.api_endpoints):
                    modules_with_api.add(module.name)

            capabilities.append(
                Capability(
                    name="rich_api",
                    description=f"Rich API with {len(system_model.api_endpoints)} endpoints",
                    capability_type="integration",
                    confidence=0.9,
                    modules=list(modules_with_api)[:5],
                    patterns=["api_endpoints"],
                    business_domain="integration",
                    complexity_score=len(system_model.api_endpoints) / 50.0,
                )
            )

        # Detect routing capability from UI routes
        if len(system_model.ui_routes) > 3:
            capabilities.append(
                Capability(
                    name="multi_page_app",
                    description=f"Multi-page application with {len(system_model.ui_routes)} routes",
                    capability_type="feature",
                    confidence=0.9,
                    modules=[],
                    patterns=["ui_routes"],
                    business_domain="navigation",
                    complexity_score=len(system_model.ui_routes) / 20.0,
                )
            )

        # Detect business domain capabilities from module business tags
        business_domains = defaultdict(set)
        for module in system_model.modules.values():
            for tag in module.business_tags:
                business_domains[tag].add(module.name)

        for domain, modules in business_domains.items():
            if len(modules) >= 2:
                capabilities.append(
                    Capability(
                        name=f"{domain}_domain",
                        description=f"Business domain: {domain}",
                        capability_type="feature",
                        confidence=0.7,
                        modules=list(modules)[:5],
                        patterns=[domain],
                        business_domain=domain,
                        complexity_score=len(modules) / 10.0,
                    )
                )

        log.info(f"Detected {len(capabilities)} additional capabilities from system model")

        return capabilities

    def enrich_system_model(self, system_model: SystemModel, chunks: List[Chunk]) -> SystemModel:
        """
        Detect capabilities and add them to the system model.

        Args:
            system_model: The system model to enrich
            chunks: Original chunks for analysis

        Returns:
            SystemModel: Enriched system model with capabilities
        """
        log.info("Enriching system model with capabilities...")

        # Detect capabilities from chunks
        chunk_capabilities = self.detect_from_chunks(chunks)

        # Detect capabilities from system model
        model_capabilities = self.detect_from_system_model(system_model)

        # Combine and deduplicate
        all_capabilities = chunk_capabilities + model_capabilities
        system_model.capabilities = all_capabilities

        # Update module capabilities
        for capability in all_capabilities:
            for module_name in capability.modules:
                if module_name in system_model.modules:
                    system_model.modules[module_name].capabilities.add(capability.name)

        log.info(f"System model enriched with {len(all_capabilities)} capabilities")

        return system_model
