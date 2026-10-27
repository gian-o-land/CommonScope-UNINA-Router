// Backend FastAPI in locale.
const API_BASE = "http://localhost:8000/api";

document.addEventListener("DOMContentLoaded", () => {
  
  // 1. Gestione robusta dell'apertura/chiusura dei menù a tendina
  function setupDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return; // Evita errori se l'elemento non è trovato

    const anchor = dropdown.querySelector('.anchor');
    anchor.addEventListener('click', (e) => {
      e.stopPropagation(); // Blocca la propagazione del click al document

      const isCurrentlyVisible = dropdown.classList.contains('visible');

      // Chiude preventivamente tutti i dropdown
      document.querySelectorAll('.dropdown-check-list').forEach(el => {
        el.classList.remove('visible');
      });

      // Se non era già aperto, aprilo
      if (!isCurrentlyVisible) {
        dropdown.classList.add('visible');
      }
    });
  }

  setupDropdown('domainDropdown');
  setupDropdown('capabilitiesDropdown');

  // 2. Chiude i dropdown se l'utente clicca fuori dalla tendina
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown-check-list')) {
      document.querySelectorAll('.dropdown-check-list').forEach(el => {
        el.classList.remove('visible');
      });
    }
  });

  // 3. Associazione delle funzioni ai pulsanti
  document.getElementById("loadToolsBtn").addEventListener("click", loadTools);
  document.getElementById("routeBtn").addEventListener("click", runRouter);
});

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
  const text = document.getElementById("queryText").value;
  const strategy = document.getElementById("strategySelect").value;
  const top_k = parseInt(document.getElementById("topKInput").value, 10);
  
  // Raccogliamo tutte le capacità spuntate
  const checkedCaps = document.querySelectorAll("#capabilitiesDropdown .items input:checked");
  const desired_capabilities = Array.from(checkedCaps).map(cb => cb.value);

  // Raccogliamo il dominio spuntato
  const checkedDomains = document.querySelectorAll("#domainDropdown .items input:checked");
  const domain = checkedDomains.length > 0 ? checkedDomains[0].value : null;

  const out = document.getElementById("routeResults");
  out.innerHTML = "Elaborazione...";
  
  try {
    const res = await fetch(`${API_BASE}/router/match`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        text,
        domain: domain,
        desired_capabilities: desired_capabilities,
        strategy: strategy,
        top_k: top_k,
        diversify_results: true
      })
    });
    
    const data = await res.json();
    out.innerHTML = "";
    
    if (data.results.length === 0) {
      out.innerHTML = "<div class='result'>Nessun tool trovato per questa configurazione.</div>";
      return;
    }

    data.results.forEach(item => {
      const div = document.createElement("div");
      div.className = "result";
      
      let reasonsHtml = `<ul class="reason-list">`;
      if (Array.isArray(item.reason)) {
        item.reason.forEach(r => { reasonsHtml += `<li>${r}</li>`; });
      } else {
        reasonsHtml += `<li>${item.reason}</li>`;
      }
      reasonsHtml += `</ul>`;

      div.innerHTML = `<strong>${item.tool_name}</strong> (${item.tool_id})
        <div class="score">Score Totale: ${item.score}</div>
        ${reasonsHtml}`;
      out.appendChild(div);
    });
  } catch (err) {
    out.innerHTML = "Errore durante il routing. Assicurati che il backend FastAPI sia in esecuzione.";
  }
}