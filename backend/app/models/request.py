from pydantic import BaseModel, Field
from typing import List, Optional

# ScopeRequest = struttura formale di una richiesta al Router.
class ScopeRequest(BaseModel):
    text: str
    desired_capabilities: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    top_k: int = 3
    strategy: str = "v5" # Possibili valori: "v0" (baseline/substrig), "v1" (token-based), "v2" (semantic-based), "v3" (hybrid), "v4" (hybrid con diversificazione), "v5" (hybrid con diversificazione e parsing dipendenze)
    diversify_results: bool = True
