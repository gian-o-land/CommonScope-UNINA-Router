from app.models.request import ScopeRequest
from app.api.router import match_scope
from benchmark.test_cases import TEST_CASES

def run_benchmarks():
    # Le strategie che vogliamo testare
    strategie = ["v0", "v1", "v2"]
    
    # Dizionario per tenere traccia dei successi
    risultati = {strat: 0 for strat in strategie}
    
    print("=== CONFRONTO STRATEGIE DI ROUTING ===\n")
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"Test {i}: {test['desc']}")
        print(f"Query: '{test['query']}'")
        print(f"Atteso: {test['expected_id']}")
        print("-" * 40)
        
        for strat in strategie:
            # Creiamo la richiesta specificando la strategia
            req = ScopeRequest(text=test["query"], top_k=1, strategy=strat)
            risposta = match_scope(req)
            
            best_match = None
            score = 0.0
            
            if risposta["results"] and risposta["results"][0]["score"] > 0:
                best_match = risposta["results"][0]["tool_id"]
                score = risposta["results"][0]["score"]
                
            esito = "✅ PASS" if best_match == test["expected_id"] else "❌ FAIL"
            
            if best_match == test["expected_id"]:
                risultati[strat] += 1
                
            print(f"  [{strat}] Ottenuto: {best_match} (Score: {score}) -> {esito}")
            
        print("=" * 60 + "\n")
    
    print("=== REPORT FINALE ACCURATEZZA ===")
    totale = len(TEST_CASES)
    for strat, successi in risultati.items():
        acc = (successi / totale) * 100
        print(f"Strategia '{strat}': {acc:.1f}% ({successi}/{totale} test superati)")

if __name__ == "__main__":
    run_benchmarks()