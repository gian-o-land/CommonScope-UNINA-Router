from fastapi import APIRouter, HTTPException
from app.models.tool import ToolRecord
from app.services.memory_store import TOOLS

router = APIRouter()

# Registry = catalogo dei tool.
# Oggi legge da TOOLS in memoria.
# Domani potrà leggere da un database vero.

@router.get("/tools")
def list_tools():
    # Restituisce tutti i tool.
    return TOOLS

@router.get("/tools/{tool_id}")
def get_tool(tool_id: str):
    # Restituisce il tool con id richiesto.
    for tool in TOOLS:
        if tool.id == tool_id:
            return tool
    raise HTTPException(status_code=404, detail="Tool not found")

@router.post("/tools")
def create_tool(tool: ToolRecord):
    # Aggiunge un nuovo tool.
    TOOLS.append(tool)
    return {"status": "created", "tool": tool}