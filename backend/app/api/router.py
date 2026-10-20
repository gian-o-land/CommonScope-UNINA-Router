import re
from fastapi import APIRouter
from app.models.request import ScopeRequest
from app.services.memory_store import get_all_tools
from sentence_transformers import SentenceTransformer, util

router = APIRouter()

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

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

# --- STRATEGIA v2: Semantic Matching ---
def score_tool_v2(tool, req: ScopeRequest) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    
    # Uniamo le parole chiave del tool per creare un "profilo" testuale
    profilo_tool = f"{tool.name} " + " ".join(tool.scope_tags + tool.capabilities + [tool.description])
    
    # Convertiamo la richiesta e il profilo in vettori matematici
    vettore_richiesta = model.encode(req.text, convert_to_tensor=True)
    vettore_tool = model.encode(profilo_tool, convert_to_tensor=True)
    
    # Calcoliamo la distanza del coseno tra i due vettori (similarità semantica)
    cosine_score = util.cos_sim(vettore_richiesta, vettore_tool).item()
    
    # Trasformiamo la similarità in un punteggio, se la similarità è sopra una certa soglia
    if cosine_score > 0.2:
        punti_semantici = cosine_score * 5.0
        score += punti_semantici
        reasons.append(f"[v2] Match Semantico ({cosine_score:.2f}) -> +{punti_semantici:.2f}")
    else:
        reasons.append(f"[v2] Affinità semantica troppo bassa ({cosine_score:.2f})")

    # Aggiungiamo i bonus statici di dominio se applicabili
    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        reasons.append(f"[v2] Boost dominio esatto: '{req.domain}' (+1.5)")

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
            case "v2":
                s, explanations = score_tool_v2(tool, req)
            
        ranked.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "score": s,
            "reason": explanations
        })
        
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {"query": req.dict(), "results": ranked[:req.top_k]}