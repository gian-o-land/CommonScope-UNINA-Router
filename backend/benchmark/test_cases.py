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
        "expected_ids": ["nlp-sentiment-local-1"], 
        "desc": "Richiesta semantica senza keyword tecniche"
    },
    {
        "query": "calcola il tragitto in macchina per Roma",
        "expected_ids": ["registry-3"], 
        "desc": "Sinonimi non previsti dai tag"
    },
    {
        "query": "Aggiungo semantic dilution per testare i limiti della strategia v2. Il database del server è esploso stamattina e abbiamo perso i dati. Il cliente è furioso. Nel frattempo, mi serve un ocr per fare un extract_text da un document cartaceo e fare sentiment_analysis sulle email di insulti.",
        "expected_ids": ["nlp-sentiment-local-1", "registry-2"], 
        "desc": "Diluizione estrema: v2 affoga nel rumore, v3 intercetta le capability esatte"
    }
]