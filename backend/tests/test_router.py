from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_match_endpoint_missing_text():
    # Simuliamo una richiesta mancante del campo obbligatorio 'text'
    payload_incompleto = {
        "strategy": "v3",
        "top_k": 3
    }
    response = client.post("/api/router/match", json=payload_incompleto)
    
    # Ci aspettiamo che FastAPI blocchi la richiesta per validazione fallita (422)
    assert response.status_code == 422
    assert "detail" in response.json()

def test_match_endpoint_happy_path():
    # Simuliamo una richiesta HTTP valida completa
    payload_valido = {
        "text": "cerco uno strumento per leggere file pdf con ocr",
        "desired_capabilities": ["extract_text"],
        "strategy": "v3",
        "top_k": 2,
        "diversify_results": True
    }
    response = client.post("/api/router/match", json=payload_valido)
    
    # Verifichiamo che il server risponda con successo (200 OK)
    assert response.status_code == 200
    
    data = response.json()
    # Verifichiamo che la struttura del JSON di ritorno sia corretta
    assert "query" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) <= 2  # Non deve superare il top_k richiesto

def test_match_endpoint_explainability_structure():
    # Verifichiamo l'integrità dei singoli oggetti nel risultato
    payload = {
        "text": "sentiment analysis",
        "strategy": "v3"
    }
    response = client.post("/api/router/match", json=payload)
    assert response.status_code == 200
    
    results = response.json()["results"]
    
    if len(results) > 0:
        primo_risultato = results[0]
        # Controllo della presenza dei campi fondamentali
        assert "tool_id" in primo_risultato
        assert "tool_name" in primo_risultato
        assert "score" in primo_risultato
        
        # Controllo critico per i requisiti del progetto: ci deve essere la spiegazione (Explainability)
        assert "reason" in primo_risultato
        assert isinstance(primo_risultato["reason"], list)
        assert len(primo_risultato["reason"]) > 0

def test_match_endpoint_invalid_strategy():
    # Simuliamo una richiesta con una strategia non supportata
    payload_invalido = {
        "text": "voglio analizzare dei dati testuali",
        "strategy": "v99" # Strategia inesistente
    }
    response = client.post("/api/router/match", json=payload_invalido)
    
    # Pydantic dovrebbe intercettare l'errore sull'Enum e restituire 422
    assert response.status_code == 422

def test_match_endpoint_out_of_domain():
    # Simuliamo una query senza alcun senso semantico o keyword tecnica
    payload_fuori_contesto = {
        "text": "zxqwerty uioplkjh asdfghjkl",
        "strategy": "v3",
        "top_k": 3
    }
    response = client.post("/api/router/match", json=payload_fuori_contesto)
    
    assert response.status_code == 200
    data = response.json()
    
    # L'algoritmo non deve forzare un instradamento se l'affinità è sotto la soglia minima
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 0        