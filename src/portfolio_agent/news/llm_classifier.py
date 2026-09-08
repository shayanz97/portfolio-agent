"""
Boundary for a future structured-output LLM classifier.

The production implementation should:
1. accept only an already-built EvidenceBundle;
2. never browse or fetch sources itself;
3. return the exact CausalClassification schema;
4. preserve INSUFFICIENT_EVIDENCE / CONFLICTING_EVIDENCE states;
5. never invent evidence item IDs or unsupported causes.

The deterministic classifier remains the safe fallback.
"""

from portfolio_agent.news.classifier import CausalClassifier
from portfolio_agent.news.models import CausalClassification, EvidenceBundle


class StructuredLlmCausalClassifier(CausalClassifier):
    def __init__(self, client):
        self.client = client

    def classify(self, bundle: EvidenceBundle) -> CausalClassification:
        raise NotImplementedError(
            "Wire a structured-output LLM client here in the deployment environment."
        )
