import re
from fastapi import APIRouter, HTTPException
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

# --- STRATEGIA v3: Hybrid Search (Token + Semantica) ---
def score_tool_v3(tool, req: ScopeRequest) -> tuple[float, list[str]]:
    score = 0.0
    reasons = ["[v3] Analisi Ibrida:"]
    
    # 1. Ricerca Esatta (Token)
    text = req.text.lower()
    parole_richiesta = set(re.findall(r'\b\w+\b', text))

    token_score = 0.0
    for tag in tool.scope_tags:
        if tag.lower() in parole_richiesta:
            token_score += 1.0
            reasons.append(f"  - Match parola chiave: '{tag}' (+1.0)")
            
    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            token_score += 2.0
            reasons.append(f"  - Match capability: '{cap}' (+2.0)")

    score += token_score

    # 2. Ricerca Semantica
    profilo_tool = f"{tool.name} " + " ".join(tool.scope_tags + tool.capabilities + [tool.description])
    vettore_richiesta = model.encode(req.text, convert_to_tensor=True)
    vettore_tool = model.encode(profilo_tool, convert_to_tensor=True)
    cosine_score = util.cos_sim(vettore_richiesta, vettore_tool).item()
    
    if cosine_score > 0.2:
        punti_semantici = cosine_score * 5.0
        score += punti_semantici
        reasons.append(f"  - Affinità Semantica ({cosine_score:.2f}) -> +{punti_semantici:.2f}")

    # 3. Boost sul Dominio (Applicato una sola volta)
    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        reasons.append(f"  - Boost dominio esatto: '{req.domain}' (+1.5)")

    if score == 0.0:
        reasons = ["[v3] Nessuna corrispondenza trovata (né esatta né semantica)."]

    return score, reasons

@router.post("/match")
def match_scope(req: ScopeRequest):
    ranked = []
    tools_attuali = get_all_tools()
    
    for tool in tools_attuali:
        match req.strategy:
            case "v0":
                s, explanations = score_tool_v0(tool, req)
            case "v1":
                s, explanations = score_tool_v1(tool, req)
            case "v2":
                s, explanations = score_tool_v2(tool, req)
            case "v3":
                s, explanations = score_tool_v3(tool, req)
            case _: # Fallback per strategie sconosciute
                raise HTTPException(status_code=422, detail="Strategia non supportata")
            
        # Filtriamo via i tool che non hanno superato i controlli (score a 0)
        if s > 0:
            ranked.append({
                "tool_id": tool.id,
                "tool_name": tool.name,
                "tags": [t.lower() for t in tool.scope_tags],
                "score": round(s, 2),
                "reason": explanations
            })
        
    # Ordiniamo prima per punteggio assoluto
    ranked.sort(key=lambda x: x["score"], reverse=True)
    
    
    final_results = diversity_ranking(ranked, req.top_k) if req.diversify_results else ranked[:req.top_k]
    
    # Puliamo l'output nascondendo la variabile d'appoggio all_tags
    for r in final_results:
        r.pop("tags", None)

    # Restituiamo il dizionario col formato corretto
    return {"query": req.model_dump(), "results": final_results}

# Algoritmo per diversificare i risultati: prende il migliore per ogni scope fino a riempire il top_k
def diversity_ranking(ranked, top_k):
    final_results = []
    visti_tags = set()
    
    # 1. Passata principale: prendiamo il migliore per ogni categoria (scope)
    for item in ranked:
        item_tags = set(item["tags"])

        # Se l'intersezione è vuota, questo tool copre ambiti completamente nuovi
        if not item_tags.intersection(visti_tags):
            final_results.append(item)
            visti_tags.update(item_tags) # Registriamo i domini appena coperti
            
        if len(final_results) == top_k:
            break
            
    # 2. Se non abbiamo riempito il top_k (perché c'erano pochi scope diversi),
    #    riempiamo i buchi rimanenti con i tool migliori scartati prima
    if len(final_results) < top_k:
        for item in ranked:
            if item not in final_results:
                final_results.append(item)
            if len(final_results) == top_k:
                break
                
    # Riordiniamo la lista finale mista in base allo score per coerenza di lettura
    final_results.sort(key=lambda x: x["score"], reverse=True)
    
    return final_results