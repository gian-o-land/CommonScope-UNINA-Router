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
      
      // Estrazione dei dati di explainability
      const exp = item.explainability;
      const b = exp.breakdown;
      const m = exp.matches;

      // Generazione Badge per i match
      const tagsHtml = m.tags.map(t => `<span class="badge tag">${t}</span>`).join('');
      const capsHtml = m.capabilities.map(c => `<span class="badge cap">${c}</span>`).join('');
      const negsHtml = m.negations_detected.map(n => `<span class="badge neg">${n}</span>`).join('');

      let matchesHtml = `<div class="matches-container">`;
      if (tagsHtml) matchesHtml += `<div><strong>Tags:</strong> ${tagsHtml}</div>`;
      if (capsHtml) matchesHtml += `<div><strong>Capabilities:</strong> ${capsHtml}</div>`;
      if (negsHtml) matchesHtml += `<div><strong>Negazioni:</strong> ${negsHtml}</div>`;
      matchesHtml += `</div>`;

      // Generazione griglia per i punteggi matematici (Breakdown)
      const breakdownHtml = `
        <div class="breakdown-grid">
          <div class="bd-item"><span>Semantica:</span> <strong>+${b.semantic_score.toFixed(2)}</strong></div>
          <div class="bd-item"><span>Keywords:</span> <strong>+${b.keyword_score.toFixed(2)}</strong></div>
          <div class="bd-item"><span>Capacità:</span> <strong>+${b.capability_score.toFixed(2)}</strong></div>
          <div class="bd-item"><span>Dominio:</span> <strong>+${b.domain_boost.toFixed(2)}</strong></div>
          ${b.penalties < 0 ? `<div class="bd-item penalty"><span>Penalità:</span> <strong>${b.penalties.toFixed(2)}</strong></div>` : ''}
        </div>
      `;

      // Log testuali nascosti in un pannello espandibile
      let logsHtml = `<ul class="reason-list">`;
      exp.logs.forEach(log => { logsHtml += `<li>${log}</li>`; });
      logsHtml += `</ul>`;

      // Assemblaggio finale dell'interfaccia di spiegazione
      const reasonsHtml = `
        <div class="explainability-box">
          <div class="exp-strategy">${exp.strategy}</div>
          <div class="exp-summary">${exp.summary}</div>
          ${breakdownHtml}
          ${matchesHtml}
          <details class="exp-logs-toggle">
            <summary>Visualizza log di tracciamento</summary>
            ${logsHtml}
          </details>
        </div>
      `;

      div.innerHTML = `
        <strong>${item.tool_name}</strong> (${item.tool_id})
        <div class="score">Score Totale: <strong>${item.score.toFixed(2)}</strong></div>
        ${reasonsHtml}
      `;
      out.appendChild(div);
    });
  } catch (err) {
    out.innerHTML = "Errore durante il routing. Assicurati che il backend FastAPI sia in esecuzione.";
  }
}