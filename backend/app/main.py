from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Router applicativi:
# - registry: catalogo dei tool
# - router: selezione dei tool più pertinenti
from app.api.registry import router as registry_router
from app.api.router import router as scope_router

# Punto di ingresso del backend.
app = FastAPI(
    title="CommonScope Starter API",
    version="0.1.0",
    description="Backend iniziale per Registry + Router in CommonScope."
)

# CORS aperto per semplificare la demo locale con il frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrazione dei moduli REST.
app.include_router(registry_router, prefix="/api/registry", tags=["registry"])
app.include_router(scope_router, prefix="/api/router", tags=["router"])

@app.get("/")
def root():
    # Root utile per chi apre 127.0.0.1:8000 nel browser.
    return {"message": "CommonScope Starter API", "health": "/api/health", "docs": "/docs"}

@app.get("/api/health")
def health():
    # Endpoint minimo di test.
    return {"status": "ok"}
