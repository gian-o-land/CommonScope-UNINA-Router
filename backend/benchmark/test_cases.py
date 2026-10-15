# Lista condivisa di casi di test per valutare i router.
# Ogni dizionario contiene la query simulata, l'ID del tool che ci
# aspettiamo vinca (o None se non deve matchare nulla) e una descrizione.

TEST_CASES = [
    {
        "query": "mi serve un ocr per leggere un pdf",
        "expected_id": "registry-2", 
        "desc": "Keyword esatta ('ocr')"
    },
    {
        "query": "voglio guardare un documentario sulla natura",
        "expected_id": None, 
        "desc": "Falso positivo per sottostringa ('document' contenuto in documentario)"
    },
    {
        "query": "devo capire se questa recensione è positiva o negativa",
        "expected_id": "nlp-sentiment-local-1", 
        "desc": "Richiesta semantica senza keyword tecniche"
    },
    {
        "query": "calcola il tragitto in macchina per Roma",
        "expected_id": "registry-3", 
        "desc": "Sinonimi non previsti dai tag (tragitto vs routing)"
    }
]