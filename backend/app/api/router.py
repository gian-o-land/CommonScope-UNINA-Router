import re
from fastapi import APIRouter, HTTPException
from app.models.request import ScopeRequest
from app.services.memory_store import TOOLS
from sentence_transformers import SentenceTransformer, util
import spacy

router = APIRouter()

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
nlp = spacy.load("it_core_news_sm")

def is_negated_spacy_v0(target_phrase: str, full_text: str) -> bool:
    """Usa l'albero delle dipendenze di spaCy per individuare le negazioni logiche."""
    doc = nlp(full_text.lower())
    parole_separate = target_phrase.lower().replace("_", " ").split()
    parole_unite = target_phrase.lower().split()
    target_words = set(parole_separate + parole_unite)
    
    for token in doc:
        # Se il token fa parte della capability cercata
        if token.text in target_words:
            # Caso 1: La parola ha una negazione diretta (es. "niente sentiment")
            if any(child.dep_ == "advmod" and child.lemma_ == "non" for child in token.children):
                return True
            
            # Caso 2: Risalita dell'intero albero sintattico per trovare un verbo
            for ancestor in token.ancestors:
                if any(child.dep_ == "advmod" and child.lemma_ == "non" for child in ancestor.children):
                    return True
                
    return False

def is_negated_spacy(target_phrase: str, full_text: str) -> bool:
    doc = nlp(full_text.lower())
    
    parole_separate = target_phrase.lower().replace("_", " ").split()
    parole_unite = target_phrase.lower().split()
    target_words = set(parole_separate + parole_unite)
    
    # Dizionario dei verbi di esclusione (lemmi base)
    verbi_escludenti = {"evitare", "ignorare", "saltare", "escludere", "omettere", "scartare"}
    # Congiunzioni che spezzano il contesto della negazione
    limiti_contesto = {"ma", "però", "tuttavia", "invece"}
    
    for token in doc:
        if token.text in target_words:
            negation_count = 0
            
            # 1. Controlliamo i figli diretti
            for child in token.children:
                if child.lemma_ in {"non", "niente", "nessun", "nessuno"}:
                    negation_count += 1
                    
            # 2. Risaliamo l'albero tenendo conto dei confini della proposizione
            current = token
            while current.dep_ != "ROOT":
                parent = current.head
                
                # Prevenzione Scope Leakage: 
                # Se incontriamo un confine logico avversativo, la negazione precedente non si propaga
                if any(child.lemma_ in limiti_contesto for child in parent.children):
                    break
                    
                # Controlliamo se il verbo reggente è un verbo escludente esplicito
                if parent.lemma_ in verbi_escludenti:
                    negation_count += 1
                    
                # Controlliamo se il verbo reggente ha un avverbio di negazione classico
                for child in parent.children:
                    if child.dep_ == "advmod" and child.lemma_ in {"non", "neanche", "nemmeno"}:
                        negation_count += 1
                        
                current = parent
                
            # Risoluzione Doppia Negazione: 
            # Pari (0, 2) -> Affermazione. Dispari (1, 3) -> Negazione.
            if negation_count % 2 != 0:
                return True
                
    return False

# --- STRATEGIA v0: Baseline (Ricerca per sottostringa) ---
def score_tool_v0(tool, req: ScopeRequest) -> tuple[float, dict]:
    score = 0.0
    explanation = {
        "strategy": "v0 (Sottostringa)", "summary": "",
        "breakdown": {"semantic_score": 0.0, "keyword_score": 0.0, "capability_score": 0.0, "domain_boost": 0.0, "penalties": 0.0},
        "matches": {"tags": [], "capabilities": [], "negations_detected": []}, "logs": []
    }
    text = req.text.lower()

    for tag in tool.scope_tags:
        if tag.lower() in text:
            score += 1.0
            explanation["breakdown"]["keyword_score"] += 1.0
            explanation["matches"]["tags"].append(tag)
            explanation["logs"].append(f"Match sottostringa su tag: '{tag}' (+1.0)")

    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            score += 2.0
            explanation["breakdown"]["capability_score"] += 2.0
            explanation["matches"]["capabilities"].append(f"{cap} (API)")
            explanation["logs"].append(f"Match capability API: '{cap}' (+2.0)")

    if req.domain and req.domain.lower() in " ".join(tool.scope_tags).lower():
        score += 1.5
        explanation["breakdown"]["domain_boost"] = 1.5
        explanation["logs"].append(f"Match domain: '{req.domain}' (+1.5)")

    explanation["summary"] = "Ammesso." if score > 0 else "Scartato: Nessuna corrispondenza."
    return score, explanation

# --- STRATEGIA v1: Tokenized ---
def score_tool_v1(tool, req: ScopeRequest) -> tuple[float, dict]:
    score = 0.0
    explanation = {
        "strategy": "v1 (Token base)", "summary": "",
        "breakdown": {"semantic_score": 0.0, "keyword_score": 0.0, "capability_score": 0.0, "domain_boost": 0.0, "penalties": 0.0},
        "matches": {"tags": [], "capabilities": [], "negations_detected": []}, "logs": []
    }
    text = req.text.lower()
    
    # Divide la frase in parole singole (token) ignorando la punteggiatura
    parole_richiesta = set(re.findall(r'\b\w+\b', text))

    for tag in tool.scope_tags:
        if tag.lower() in parole_richiesta:
            score += 1.0
            explanation["breakdown"]["keyword_score"] += 1.0
            explanation["matches"]["tags"].append(tag)
            explanation["logs"].append(f"Match parola chiave esatta: '{tag}' (+1.0)")

    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            score += 2.0
            explanation["breakdown"]["capability_score"] += 2.0
            explanation["matches"]["capabilities"].append(f"{cap} (API)")
            explanation["logs"].append(f"Match capability API: '{cap}' (+2.0)")

    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        explanation["breakdown"]["domain_boost"] = 1.5
        explanation["logs"].append(f"Match domain: '{req.domain}' (+1.5)")

    explanation["summary"] = "Ammesso." if score > 0 else "Scartato: Nessuna corrispondenza."  

    return score, explanation

# --- STRATEGIA v2: Semantic Matching ---
def score_tool_v2(tool, req: ScopeRequest) -> tuple[float, dict]:
    score = 0.0
    explanation = {
        "strategy": "v2 (Semantica)", "summary": "",
        "breakdown": {"semantic_score": 0.0, "keyword_score": 0.0, "capability_score": 0.0, "domain_boost": 0.0, "penalties": 0.0},
        "matches": {"tags": [], "capabilities": [], "negations_detected": []}, "logs": []
    }
    
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
        explanation["breakdown"]["semantic_score"] = round(punti_semantici, 2)
        explanation["logs"].append(f"Match Semantico ({cosine_score:.2f}) -> +{punti_semantici:.2f}")
    else:
        explanation["logs"].append(f"Affinità semantica troppo bassa ({cosine_score:.2f})")
    # Aggiungiamo i bonus statici di dominio se applicabili
    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        explanation["breakdown"]["domain_boost"] = 1.5
        explanation["logs"].append(f"Match domain: '{req.domain}' (+1.5)")

    explanation["summary"] = "Ammesso." if score > 0 else "Scartato: Nessuna corrispondenza semantica."
    return score, explanation

# --- STRATEGIA v3: Hybrid Search (Token + Semantica) ---
def score_tool_v3(tool, req: ScopeRequest) -> tuple[float, dict]:
    score = 0.0
    explanation = {
        "strategy": "v3 (Ibrida Base)", "summary": "",
        "breakdown": {"semantic_score": 0.0, "keyword_score": 0.0, "capability_score": 0.0, "domain_boost": 0.0, "penalties": 0.0},
        "matches": {"tags": [], "capabilities": [], "negations_detected": []}, "logs": []
    }
    
    # 1. Ricerca Esatta (Token)
    text = req.text.lower()
    parole_richiesta = set(re.findall(r'\b\w+\b', text))

    token_score = 0.0
    for tag in tool.scope_tags:
        if tag.lower() in parole_richiesta:
            token_score += 1.0
            explanation["breakdown"]["keyword_score"] += 1.0
            explanation["matches"]["tags"].append(tag)
            explanation["logs"].append(f"Match parola chiave: '{tag}' (+1.0)")
            
    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            token_score += 2.0
            explanation["breakdown"]["capability_score"] += 2.0
            explanation["matches"]["capabilities"].append(cap)
            explanation["logs"].append(f"Match capability: '{cap}' (+2.0)")

    score += token_score

    # 2. Ricerca Semantica
    profilo_tool = f"{tool.name} " + " ".join(tool.scope_tags + tool.capabilities + [tool.description])
    vettore_richiesta = model.encode(req.text, convert_to_tensor=True)
    vettore_tool = model.encode(profilo_tool, convert_to_tensor=True)
    cosine_score = util.cos_sim(vettore_richiesta, vettore_tool).item()
    
    if cosine_score > 0.2:
        punti_semantici = cosine_score * 5.0
        score += punti_semantici
        explanation["breakdown"]["semantic_score"] += punti_semantici
        explanation["logs"].append(f"Affinità Semantica ({cosine_score:.2f}) -> +{punti_semantici:.2f}")

    # 3. Boost sul Dominio (Applicato una sola volta)
    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        explanation["breakdown"]["domain_boost"] += 1.5
        explanation["logs"].append(f"Boost dominio esatto: '{req.domain}' (+1.5)")

    explanation["summary"] = "Ammesso." if score > 0 else "Scartato: Nessuna corrispondenza."

    return score, explanation

# --- STRATEGIA v4: Hybrid Search con diversificazione ---
def score_tool_v4(tool, req: ScopeRequest) -> tuple[float, dict]:
    score = 0.0
    explanation = {
        "strategy": "v4 (Deep Capability Scanning)", "summary": "",
        "breakdown": {"semantic_score": 0.0, "keyword_score": 0.0, "capability_score": 0.0, "domain_boost": 0.0, "penalties": 0.0},
        "matches": {"tags": [], "capabilities": [], "negations_detected": []}, "logs": []
    }

    # 1. Ricerca Esatta (Token e Testo Libero)
    text = req.text.lower()
    parole_richiesta = set(re.findall(r'\b\w+\b', text))
    token_score = 0.0

    # 1° differenza con v3: Depotenziamento dei tag generici (+0.5 invece di +1.0)
    for tag in tool.scope_tags:
        if tag.lower() in parole_richiesta:
            token_score += 0.5
            explanation["breakdown"]["keyword_score"] += 0.5
            explanation["matches"]["tags"].append(tag)
            explanation["logs"].append(f"Match tag generico: '{tag}' (+0.5)")
            
    # 2° differenza con v3: Scansione profonda delle capabilities nel testo libero
    for cap in tool.capabilities:
        cap_testuale = cap.lower().replace("_", " ")
        if cap.lower() in text or cap_testuale in text:
            token_score += 2.0
            explanation["breakdown"]["capability_score"] += 2.0
            explanation["matches"]["capabilities"].append(cap)
            explanation["logs"].append(f"Match capability nel testo: '{cap}' (+2.0)")

    # Manteniamo il controllo API esplicito
    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            token_score += 2.0
            explanation["breakdown"]["capability_score"] += 2.0
            explanation["matches"]["capabilities"].append(cap)
            explanation["logs"].append(f"Match capability richiesta API: '{cap}' (+2.0)")

    score += token_score

    # 2. Ricerca Semantica
    profilo_tool = f"{tool.name} " + " ".join(tool.scope_tags + tool.capabilities + [tool.description])
    vettore_richiesta = model.encode(req.text, convert_to_tensor=True)
    vettore_tool = model.encode(profilo_tool, convert_to_tensor=True)
    cosine_score = util.cos_sim(vettore_richiesta, vettore_tool).item()
    
    if cosine_score > 0.2:
        punti_semantici = cosine_score * 5.0
        score += punti_semantici
        explanation["breakdown"]["semantic_score"] += punti_semantici
        explanation["logs"].append(f"Affinità Semantica ({cosine_score:.2f}) -> +{punti_semantici:.2f}")

    # 3. Boost sul Dominio
    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        explanation["breakdown"]["domain_boost"] += 1.5
        explanation["logs"].append(f"Boost dominio esatto: '{req.domain}' (+1.5)")

    explanation["summary"] = "Ammesso." if score > 0 else "Scartato: Nessuna corrispondenza."
    return score, explanation

# --- STRATEGIA v5: Hybrid Search + Dependency Parsing Strutturato ---
def score_tool_v5(tool, req: ScopeRequest) -> tuple[float, dict]:
    score = 0.0
    
    # Inizializzazione dell'oggetto di Explainability Strutturata
    explanation = {
        "strategy": "v5 (Hybrid + Dependency Parsing)",
        "summary": "",
        "breakdown": {
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "capability_score": 0.0,
            "domain_boost": 0.0,
            "penalties": 0.0
        },
        "matches": {
            "tags": [],
            "capabilities": [],
            "negations_detected": []
        },
        "logs": []
    }
    
    text = req.text.lower()
    parole_richiesta_set = set(re.findall(r'\b\w+\b', text))
    token_score = 0.0

    # 1. Scansione Tag 
    for tag in tool.scope_tags:
        if tag.lower() in parole_richiesta_set:
            if is_negated_spacy(tag.lower(), text):
                token_score -= 2.0
                explanation["breakdown"]["penalties"] -= 2.0
                explanation["matches"]["negations_detected"].append(tag)
                explanation["logs"].append(f"Tag negato: '{tag}' (-2.0)")
            else:
                token_score += 0.5
                explanation["breakdown"]["keyword_score"] += 0.5
                explanation["matches"]["tags"].append(tag)
                explanation["logs"].append(f"Match tag: '{tag}' (+0.5)")

    # 2. Deep Capability Scanning 
    for cap in tool.capabilities:
        cap_testuale = cap.lower().replace("_", " ")
        if cap.lower() in text or cap_testuale in text:
            target = cap.lower() if cap.lower() in text else cap_testuale
            if is_negated_spacy(target, text):
                token_score -= 5.0
                explanation["breakdown"]["penalties"] -= 5.0
                explanation["matches"]["negations_detected"].append(cap)
                explanation["logs"].append(f"Capability negata: '{cap}' (-5.0)")
            else:
                token_score += 2.0
                explanation["breakdown"]["capability_score"] += 2.0
                explanation["matches"]["capabilities"].append(cap)
                explanation["logs"].append(f"Capability testuale: '{cap}' (+2.0)")

    # 3. Controllo API esplicito
    for cap in req.desired_capabilities:
        if cap in tool.capabilities:
            token_score += 2.0
            explanation["breakdown"]["capability_score"] += 2.0
            explanation["matches"]["capabilities"].append(f"{cap} (API)")
            explanation["logs"].append(f"Capability API: '{cap}' (+2.0)")

    score += token_score

    # 4. Ricerca Semantica
    profilo_tool = f"{tool.name} " + " ".join(tool.scope_tags + tool.capabilities + [tool.description])
    vettore_richiesta = model.encode(req.text, convert_to_tensor=True)
    vettore_tool = model.encode(profilo_tool, convert_to_tensor=True)
    cosine_score = util.cos_sim(vettore_richiesta, vettore_tool).item()
    
    if cosine_score > 0.2:
        punti_semantici = cosine_score * 5.0
        score += punti_semantici
        explanation["breakdown"]["semantic_score"] = round(punti_semantici, 2)
        explanation["logs"].append(f"Affinità Semantica ({cosine_score:.2f}) -> +{punti_semantici:.2f}")

    # 5. Boost sul Dominio
    if req.domain and req.domain.lower() in [t.lower() for t in tool.scope_tags]:
        score += 1.5
        explanation["breakdown"]["domain_boost"] = 1.5
        explanation["logs"].append(f"Boost dominio esatto: '{req.domain}' (+1.5)")

    if score <= 0.0:
        explanation["summary"] = "Scartato: punteggio nullo o penalità per negazione prevalenti."
        return 0.0, explanation

    explanation["summary"] = "Ammesso: profilo corrispondente alle richieste."
    return score, explanation

@router.post("/match")
def match_scope(req: ScopeRequest):
    ranked = []
    
    for tool in TOOLS:
        match req.strategy:
            case "v0": s, exp = score_tool_v0(tool, req)
            case "v1": s, exp = score_tool_v1(tool, req)
            case "v2": s, exp = score_tool_v2(tool, req)
            case "v3": s, exp = score_tool_v3(tool, req)
            case "v4": s, exp = score_tool_v4(tool, req)
            case "v5": s, exp = score_tool_v5(tool, req)
            case _: raise HTTPException(status_code=422, detail="Strategia non supportata")
            
        if s > 0:
            ranked.append({
                "tool_id": tool.id,
                "tool_name": tool.name,
                "tags": [t.lower() for t in tool.scope_tags],
                "score": round(s, 2),
                "explainability": exp # Rinominato da reason per maggiore chiarezza[cite: 16]
            })
        
    ranked.sort(key=lambda x: x["score"], reverse=True)
    final_results = diversity_ranking(ranked, req.top_k) if req.diversify_results else ranked[:req.top_k]
    
    for r in final_results:
        r.pop("tags", None)

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