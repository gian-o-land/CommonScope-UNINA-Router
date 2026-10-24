// Backend FastAPI in locale.
const API_BASE = "http://localhost:8000/api";

async function loadTools() {
  // Carica i tool dal Registry.
  const toolsList = document.getElementById("toolsList");
  toolsList.innerHTML = "<li>Caricamento...</li>";
  try {
    const res = await fetch(`${API_BASE}/registry/tools`);
    const data = await res.json();
    toolsList.innerHTML = "";
    data.forEach(tool => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${tool.name}</strong> — ${tool.description}`;
      toolsList.appendChild(li);
    });
  } catch (err) {
    toolsList.innerHTML = "<li>Errore nel caricamento dei tool</li>";
  }
}

async function runRouter() {
  // Esegue una query verso il Router e mostra i risultati.
  const text = document.getElementById("queryText").value;
  const domain = document.getElementById("domainText").value.trim();
  const out = document.getElementById("routeResults");
  out.innerHTML = "Elaborazione...";
  try {
    const res = await fetch(`${API_BASE}/router/match`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        text,
        domain: domain || null,
        desired_capabilities: [],
        top_k: 3
      })
    });
    const data = await res.json();
    out.innerHTML = "";
    data.results.forEach(item => {
      const div = document.createElement("div");
      div.className = "result";
      div.innerHTML = `<strong>${item.tool_name}</strong>
        <div class="score">Score: ${item.score}</div>
        <div>${item.reason}</div>`;
      out.appendChild(div);
    });
  } catch (err) {
    out.innerHTML = "Errore durante il routing.";
  }
}

// Associa i pulsanti alle funzioni.
document.getElementById("loadToolsBtn").addEventListener("click", loadTools);
document.getElementById("routeBtn").addEventListener("click", runRouter);