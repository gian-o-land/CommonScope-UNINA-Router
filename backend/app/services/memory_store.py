from app.models.tool import ToolRecord

# Questo file simula un database.
# TOOLS contiene i tool concreti caricati nel prototipo.
# Differenza chiave:
# - ToolRecord (tool.py) = schema della carta di identità
# - TOOLS (qui) = carte di identità reali già compilate
TOOLS = [
    ToolRecord(
        id="registry-1",
        name="ImageClassifier",
        description="Classifica immagini in categorie predefinite",
        version="0.1.0",
        scope_tags=["vision", "classification"],
        capabilities=["classify_image", "return_top_label"],
        input_schema={"type": "image"},
        output_schema={"type": "label"},
        endpoint="http://localhost:8000/mock/image-classifier",
        status="active",
        owner="lab"
    ),
    ToolRecord(
        id="registry-2",
        name="OCRTool",
        description="Estrae testo da documenti e immagini",
        version="0.1.0",
        scope_tags=["vision", "document", "ocr"],
        capabilities=["extract_text", "parse_document"],
        input_schema={"type": "image_or_pdf"},
        output_schema={"type": "text"},
        endpoint="http://localhost:8000/mock/ocr",
        status="active",
        owner="lab"
    ),
    ToolRecord(
        id="registry-3",
        name="RoutePlanner",
        description="Calcola percorsi e tragitti",
        version="0.1.0",
        scope_tags=["planning", "maps", "routing"],
        capabilities=["plan_route", "estimate_distance"],
        input_schema={"type": "locations"},
        output_schema={"type": "route"},
        endpoint="http://localhost:8000/mock/route",
        status="active",
        owner="lab"
    ),
    ToolRecord(
        id="registry-4",
        name="SentimentAnalyzer BERT",
        description="Modello NLP per estrarre la polarità emotiva da testi brevi.",
        version="0.1.0",
        scope_tags=["nlp", "text"],
        capabilities=["analyze_sentiment", "return_polarity"],
        input_schema={"type": "text"},
        output_schema={"type": "sentiment"},
        endpoint="http://localhost:8000/mock/sentiment",
        status="active",
        owner="lab"
    ),
    ToolRecord(
        id="registry-5",
        name="Financial Data Scraper",
        description="Analizza documenti testuali per estrarre trend finanziari.",
        version="0.1.0",
        scope_tags=["data", "analysis"],
        capabilities=["scrape_financial_data", "return_trends"],
        input_schema={"type": "text"},
        output_schema={"type": "financial_trends"},
        endpoint="http://localhost:8000/mock/finance",
        status="active",
        owner="lab"
    ),
    ToolRecord(
        id="registry-6",
        name="AudioTranscriber Whisper",
        description="Trascrive file audio vocali in testo e li traduce.",
        version="0.1.0",
        scope_tags=["audio", "nlp"],
        capabilities=["transcribe_audio", "translate_text"],
        input_schema={"type": "audio"}, 
        output_schema={"type": "text"},
        endpoint="http://localhost:8000/mock/audio-transcriber",
        status="active",
        owner="lab"
    )
]

def get_all_tools() -> list[ToolRecord]:
    """Restituisce tutti i tool registrati."""
    return TOOLS