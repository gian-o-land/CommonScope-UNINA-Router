from app.models.request import ScopeRequest
from app.api.router import match_scope
from benchmark.test_cases import TEST_CASES

def run_benchmarks():
    # Le strategie che vogliamo testare
    strategie = ["v0", "v1", "v2", "v3", "v4", "v5"]
    
    # Dizionario per tenere traccia dei successi
    risultati = {strat: 0 for strat in strategie}
    
    print("=== CONFRONTO STRATEGIE DI ROUTING ===\n")
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"Test {i}: {test['desc']}")
        print(f"Query: '{test['query']}'")
        print(f"Atteso: {test['expected_ids']}")
        print("-" * 50)

        k_necessari = max(1, len(test["expected_ids"]))
        
        for strat in strategie:
            # Estraiamo dinamicamente il flag diversificazione se presente, altrimenti usiamo False
            usa_diversificazione = test.get("diversify_results", False)
            
            # Creiamo la richiesta specificando la strategia
            req = ScopeRequest(text=test["query"], top_k=k_necessari, strategy=strat, diversify_results=usa_diversificazione)
            risposta = match_scope(req)
            
            # Estraiamo tutti gli ID che hanno uno score > 0
            ottenuti_ids = [res["tool_id"] for res in risposta["results"] if res["score"] > 0]

            #Estrazione dettagliata dei risultati ottenuti
            ottenuti_dettagliati = [f"{res['tool_id']} ({res['score']:.2f})" for res in risposta["results"] if res["score"] > 0]
            
            # Un test passa se restituisce ESATTAMENTE gli elementi richiesti (ignorando l'ordine)
            esito_ok = set(ottenuti_ids) == set(test["expected_ids"])
            
            esito = "✅ PASS" if esito_ok else "❌ FAIL"
            if esito_ok:
                risultati[strat] += 1
                
            print(f"  [{strat}] Ottenuti: {ottenuti_dettagliati} -> {esito}")
            
        print("=" * 60 + "\n")
    
    print("=== REPORT FINALE ACCURATEZZA ===")
    totale = len(TEST_CASES)
    for strat, successi in risultati.items():
        acc = (successi / totale) * 100
        print(f"Strategia '{strat}': {acc:.1f}% ({successi}/{totale} test superati)")

if __name__ == "__main__":
    run_benchmarks()