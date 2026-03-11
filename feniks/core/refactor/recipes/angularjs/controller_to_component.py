import os
import httpx
import json
from typing import Any, Dict, List, Optional
from feniks.core.models.types import Chunk, SystemModel
from feniks.core.refactor.recipe import FileChange, RefactorPlan, RefactorRecipe, RefactorResult, RefactorRisk
from feniks.infra.logging import get_logger

log = get_logger("refactor.recipes.angularjs.ai_powered")

OLLAMA_URL = 'http://host.docker.internal:11434/api/generate'

class ControllerToComponentRecipe(RefactorRecipe):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.writer_model = 'qwen2.5:14b'
        self.auditor_model = 'deepseek-coder-v2:16b'

    @property
    def name(self) -> str:
        return "angularjs.ai-powered-migration"

    @property
    def description(self) -> str:
        return "Migrate AngularJS to Next.js using 14B/16B AI models with AST awareness"

    @property
    def risk_level(self) -> RefactorRisk:
        return RefactorRisk.MEDIUM

    def _ask_ai(self, model: str, prompt: str) -> str:
        try:
            payload = {'model': model, 'prompt': prompt, 'stream': False}
            resp = httpx.post(OLLAMA_URL, json=payload, timeout=600.0)
            return resp.json().get('response', '').strip()
        except Exception as e:
            log.error(f"AI Error ({model}): {e}")
            return ""

    def analyze(self, system_model: SystemModel, target: Optional[Dict[str, Any]] = None) -> Optional[RefactorPlan]:
        # Logika wyboru plików z SystemModel (Feniks!)
        target_files = []
        for mod in system_model.modules.values():
            target_files.extend(mod.file_paths)
        
        return RefactorPlan(
            recipe_name=self.name,
            project_id=system_model.project_id,
            target_modules=[],
            target_files=target_files,
            rationale="AI-driven modular migration",
            risks=["Semantic drift"],
            risk_level=self.risk_level,
            estimated_changes=len(target_files),
            validation_steps=["AI Audit", "TS Compile"]
        )

    def execute(self, plan: RefactorPlan, chunks: List[Chunk], dry_run: bool = True) -> RefactorResult:
        result = RefactorResult(plan=plan, success=True)
        
        for chunk in chunks:
            log.info(f"AI Modernizing: {chunk.file_path}")
            
            # 1. WRITER (Qwen 14B)
            prompt = f"Convert this AngularJS code to Next.js TypeScript. Use @/lib/api. Split into hooks if needed. Code only:\n{chunk.text}"
            converted_code = self._ask_ai(self.writer_model, prompt)
            
            # 2. AUDITOR (DeepSeek 16B)
            audit_prompt = f"Audit this conversion. Compare Legacy vs New. Return PASS or FAIL with reason.\n\nLEGACY:\n{chunk.text}\n\nNEW:\n{converted_code}"
            audit_res = self._ask_ai(self.auditor_model, audit_prompt)
            
            if "PASS" in audit_res.upper():
                result.file_changes.append(FileChange(
                    file_path=chunk.file_path.replace('.js', '.ts'),
                    original_content=chunk.text,
                    modified_content=converted_code,
                    change_type="modify"
                ))
            else:
                log.warning(f"Audit FAILED for {chunk.file_path}: {audit_res[:100]}")
                result.warnings.append(f"{chunk.file_path}: {audit_res[:100]}")

        return result

    def validate(self, result: RefactorResult) -> bool:
        return len(result.errors) == 0

