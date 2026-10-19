import re
from fastapi import APIRouter
from app.models.request import ScopeRequest
from app.services.memory_store import get_all_tools

router = APIRouter()

# --- STRATEGIA v0: Baseline (Ricerca per sottostringa) ---
def score_tool_v0(tool, req: ScopeRequest) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    text = req.text.lower()

    for tag in tool.scope_tags:
        if tag.lower() in text:
            score += 1.0
            reasons.append(f"[v0] Match sottostringa su tag: '{tag}' (+1.0)")

    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            score += 2.0
            reasons.append(f"[v0] Match capability: '{cap}' (+2.0)")

    if req.domain and req.domain.lower() in " ".join(tool.scope_tags).lower():
        score += 1.5
        reasons.append(f"[v0] Match domain: '{req.domain}' (+1.5)")

    if score == 0.0:
        reasons.append("[v0] Nessuna corrispondenza trovata.")

    return score, reasons

# --- STRATEGIA v1: Tokenized ---
def score_tool_v1(tool, req: ScopeRequest) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    text = req.text.lower()
    
    # Divide la frase in parole singole (token) ignorando la punteggiatura
    parole_richiesta = set(re.findall(r'\b\w+\b', text))

    for tag in tool.scope_tags:
        if tag.lower() in parole_richiesta:
            score += 1.0
            reasons.append(f"[v1] Match parola chiave esatta: '{tag}' (+1.0)")

    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            score += 2.0
            reasons.append(f"[v1] Match capability: '{cap}' (+2.0)")

    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        reasons.append(f"[v1] Match domain: '{req.domain}' (+1.5)")

    if score == 0.0:
        reasons.append("[v1] Nessuna corrispondenza trovata.")    

    return score, reasons


@router.post("/match")
def match_scope(req: ScopeRequest):
    ranked = []
    tools_attuali = get_all_tools()
    
    for tool in tools_attuali:
        # Selettore di strategia
        match req.strategy:
            case "v0":
                s, explanations = score_tool_v0(tool, req)
            case "v1":
                s, explanations = score_tool_v1(tool, req)
            
        ranked.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "score": s,
            "reason": explanations
        })
        
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {"query": req.dict(), "results": ranked[:req.top_k]}