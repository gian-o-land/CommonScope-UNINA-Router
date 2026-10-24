# Lista condivisa di casi di test per valutare i router.
# Ogni dizionario contiene la query simulata, l'ID del tool che ci
# aspettiamo vinca (o None se non deve matchare nulla) e una descrizione.

TEST_CASES = [
    {
        "query": "mi serve un ocr per leggere un pdf",
        "expected_ids": ["registry-2"], 
        "desc": "Keyword esatta ('ocr')"
    },
    {
        "query": "voglio guardare un documentario sulla natura",
        "expected_ids": [], # Nessun tool atteso 
        "desc": "Falso positivo per sottostringa"
    },
    {
        "query": "devo capire se questa recensione è positiva o negativa",
        "expected_ids": ["registry-4"], 
        "desc": "Richiesta semantica senza keyword tecniche"
    },
    {
        "query": "calcola il tragitto in macchina per Roma",
        "expected_ids": ["registry-3"], 
        "desc": "Sinonimi non previsti dai tag"
    },
    {
        "query": "Aggiungo semantic dilution per testare i limiti della strategia v2. Stamattina abbiamo perso i dati. Il cliente è furioso. Nel frattempo, mi serve un ocr per fare un extract_text da un document cartaceo e fare sentiment_analysis sulle email di insulti.",
        "expected_ids": ["registry-4", "registry-2"], 
        "desc": "Diluizione estrema: v2 affoga nel rumore, v3 intercetta le capability esatte"
    },
    {
        "query": "ho una registrazione vocale, puoi tradurre quello che dicono?",
        "expected_ids": ["registry-6"], 
        "desc": "Recupero cross-domain (Audio + NLP) senza keyword esatte"
    },
    {
        "query": "estrai il testo da questa scansione e fai la sentiment analysis",
        "expected_ids": ["registry-2", "registry-4"], 
        "desc": "Test per Diversity Ranking: evita il distrattore registry-5 ed estrae la pipeline OCR + NLP",
        "diversify_results": True
    },
    {
        "query": "Non mi interessa un tool in grado di eseguire la analize sentiment dei messaggi, voglio solo calcolare il tragitto in macchina per allontanarmi da qui.",
        "expected_ids": ["registry-3"], 
        "desc": "Adversarial Test: Negazione esplicita di una capability (v4 Trap)",
        "diversify_results": False
    }
]