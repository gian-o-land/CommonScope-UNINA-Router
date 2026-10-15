from app.models.request import ScopeRequest
from app.api.router import match_scope
from benchmark.test_cases import TEST_CASES

def run_benchmarks():
    successi = 0
    print("--- AVVIO BENCHMARK BASELINE (Router v0) ---\n")
    
    for i, test in enumerate(TEST_CASES, 1):
        # Simuliamo una richiesta con top_k=1 per prendere solo il risultato migliore
        req = ScopeRequest(text=test["query"], top_k=1)
        risposta = match_scope(req)
        
        # Estraiamo l'ID del tool vincitore (se ha ottenuto un punteggio > 0)
        best_match = None
        if risposta["results"] and risposta["results"][0]["score"] > 0:
            best_match = risposta["results"][0]["tool_id"]
            
        if best_match == test["expected_id"]:
            successi += 1
            esito = "✅ PASS"
        else:
            esito = "❌ FAIL"
        
        print(f"Test {i}: {test['desc']}")
        print(f"  Query: '{test['query']}'")
        print(f"  Atteso: {test['expected_id']} | Ottenuto: {best_match}")
        print(f"  Esito: {esito}\n")

    accuracy = (successi / len(TEST_CASES)) * 100
    print(f"--- RISULTATO FINALE: Accuratezza {accuracy:.1f}% ---")

if __name__ == "__main__":
    run_benchmarks()