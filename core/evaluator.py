# core/evaluator.py
import dataclasses
import json
from typing import List, Dict, Any, Optional

@dataclasses.dataclass
class EvaluationReport:
    task_id: str
    score: float  # 0.0 to 1.0
    metrics: Dict[str, Any]
    reasoning: str
    token_usage: Dict[str, int]
    status: str = "success"

class PhoenixEvaluator:
    """Mikro-Evaluator dla modułu Phoenix (Code Generation/Refactor)."""
    
    def evaluate_code(self, original_code: str, generated_code: str, plan: str) -> EvaluationReport:
        # Tu w przyszłości wejdzie Qwen/Llama do oceny
        # Na razie implementujemy szkielet raportowania
        
        # Przykładowe metryki
        diff_size = len(generated_code) - len(original_code)
        
        return EvaluationReport(
            task_id="pending",
            score=0.9, # Placeholder
            metrics={
                "diff_size": diff_size,
                "syntax_valid": True,
                "matches_plan": True
            },
            reasoning="Kod jest zgodny z planem, zachowano strukturę klas.",
            token_usage={"input": 0, "output": 0} # Do uzupełnienia przez brokera
        )

    def save_to_lab(self, report: EvaluationReport):
        """Przesyła raport do RAE-Lab i RAE-Memory."""
        print(f"🔬 Phoenix Insight: Score {report.score} for task {report.task_id}")
        # Logika zapisu w JSON w katalogu RAE-Lab
