from rae_core.models.evidence import DecisionEvidenceRecord
from rae_core.models.cost import CostVector

def create_plan_evidence(summary: str, reasoning: str, confidence: float, tokens: int) -> DecisionEvidenceRecord:
    """Wraps Phoenix planning logic into a v3 DecisionEvidenceRecord."""
    return DecisionEvidenceRecord(
        decision_summary=summary,
        reasoning_summary=reasoning,
        confidence=confidence,
        cost_vector=CostVector(input_tokens=tokens)
    )
