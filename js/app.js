/* ============================================================
   Cognitive Logic — AI Compliance Copilot
   Backend: https://api.cognitivelogic.it
   ============================================================ */

const API_URL = "https://api.cognitivelogic.it/analyze";
const PDF_URL = "https://api.cognitivelogic.it/export-pdf";

const inputEl      = document.getElementById("chat-input");
const analyzeBtn   = document.getElementById("analyze-btn");
const clearBtn     = document.getElementById("clear-btn");
const pdfBtn       = document.getElementById("pdf-btn");
const statusLine   = document.getElementById("status-line");

const decisionBox            = document.getElementById("decision-box");
const riskLevelEl            = document.getElementById("risk-level");
const riskScoreEl            = document.getElementById("risk-score");
const whyEl                  = document.getElementById("why");
const impactEl               = document.getElementById("impact");
const summaryEl              = document.getElementById("summary");
const euClassificationEl     = document.getElementById("eu-classification");
const gapsListEl             = document.getElementById("gaps-list");
const recommendationsListEl  = document.getElementById("recommendations-list");
const rawOutputEl            = document.getElementById("raw-output");

const euObligations          = document.getElementById("eu-obligations");
const euControls             = document.getElementById("eu-controls");
const euRegulatoryObligations= document.getElementById("eu-regulatory-obligations");
const euArticles             = document.getElementById("eu-articles");

/* ── Helpers ──────────────────────────────────────────────── */

function safeSet(el, value) {
  if (el) el.textContent = value;
}

function safeHtml(el, html) {
  if (el) el.innerHTML = html;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setList(element, items) {
  if (!element) return;
  if (!Array.isArray(items) || items.length === 0) {
    element.innerHTML = "<li>Nessun elemento rilevato.</li>";
    return;
  }
  element.innerHTML = items
    .map(item => `<li>${escapeHtml(String(item))}</li>`)
    .join("");
}

function setDecisionUI(level, fallbackText = "") {
  if (!decisionBox) return;
  decisionBox.classList.remove("decision-high", "decision-medium", "decision-low");

  if (level === "HIGH") {
    decisionBox.classList.add("decision-high");
    decisionBox.innerText = fallbackText || "CRITICAL — intervento immediato richiesto";
  } else if (level === "MEDIUM") {
    decisionBox.classList.add("decision-medium");
    decisionBox.innerText = fallbackText || "ACTION REQUIRED — controlli mancanti";
  } else {
    decisionBox.classList.add("decision-low");
    decisionBox.innerText = fallbackText || "MONITOR — rischio contenuto";
  }
}

function resetOutput() {
  setDecisionUI("LOW", "In attesa di analisi");
  safeSet(riskLevelEl, "—");
  safeSet(riskScoreEl, "—");
  safeSet(whyEl, "—");
  safeSet(impactEl, "—");
  safeSet(summaryEl, "Nessuna analisi ancora eseguita.");
  safeSet(euClassificationEl, "—");
  safeHtml(gapsListEl, "<li>—</li>");
  safeHtml(recommendationsListEl, "<li>—</li>");
  safeHtml(euObligations, "<li>—</li>");
  safeHtml(euControls, "<li>—</li>");
  safeHtml(euRegulatoryObligations, "<li>—</li>");
  safeSet(euArticles, "—");
  safeSet(rawOutputEl, "In attesa di risposta backend.");
  safeSet(statusLine, "Scrivi una descrizione e avvia l'analisi.");
}

/* ── Analyze ──────────────────────────────────────────────── */

async function sendMessage() {
  const text = inputEl.value.trim();

  if (!text) {
    safeSet(statusLine, "Inserisci una descrizione del sistema AI.");
    inputEl.focus();
    return;
  }

  analyzeBtn.disabled = true;
  clearBtn.disabled = true;
  pdfBtn.disabled = true;

  safeSet(statusLine, "Analisi in corso…");
  if (decisionBox) decisionBox.textContent = "Elaborazione…";
  safeSet(riskLevelEl, "…");
  safeSet(riskScoreEl, "…");
  safeSet(whyEl, "Il backend sta elaborando i segnali rilevati.");
  safeSet(impactEl, "Valutazione impatto in corso.");
  safeSet(summaryEl, "Il backend sta elaborando la richiesta.");
  safeSet(euClassificationEl, "N/A");
  safeHtml(gapsListEl, "<li>Analisi in corso…</li>");
  safeHtml(recommendationsListEl, "<li>Analisi in corso…</li>");
  safeSet(rawOutputEl, "Richiesta inviata a " + API_URL);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "CL-qen-2026-xK9mPvZ3nRwQ7tYbDjF"
      },
      body: JSON.stringify({ system: text, context: "EU" })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.error || "Errore backend");
    }

    const riskLevel = data.risk_level || "LOW";
    const riskScore = data.risk_score ?? "—";
    const summary   = data.summary || "Analisi completata.";
    const gaps      = Array.isArray(data.gaps) ? data.gaps : [];
    const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];

    let why = data.why;
    if (!why) {
      why = gaps.length > 0
        ? "Il sistema presenta segnali di rischio legati ai controlli o ai dati indicati."
        : "Non sono emersi gap significativi nella descrizione fornita.";
    }

    let impact = data.impact;
    if (!impact) {
      if (riskLevel === "HIGH") {
        impact = "Il sistema richiede interventi rapidi prima di essere presentato come iniziativa conforme.";
      } else if (riskLevel === "MEDIUM") {
        impact = "Il sistema può evolvere con controlli aggiuntivi e maggiore tracciabilità.";
      } else {
        impact = "Il sistema appare gestibile, con monitoraggio e controlli di base.";
      }
    }

    let decision = data.decision;
    if (!decision) {
      if (riskLevel === "HIGH") {
        decision = "CRITICAL — intervento immediato richiesto";
      } else if (riskLevel === "MEDIUM") {
        decision = "ACTION REQUIRED — controlli mancanti";
      } else {
        decision = "MONITOR — rischio contenuto";
      }
    }

    setDecisionUI(riskLevel, decision);
    safeSet(riskLevelEl, String(riskLevel).toUpperCase());
    safeSet(riskScoreEl, String(riskScore));
    safeSet(whyEl, why);
    safeSet(impactEl, impact);
    safeSet(summaryEl, summary);
    safeSet(euClassificationEl, data.eu_classification || "Non disponibile");

    setList(gapsListEl, gaps);
    setList(recommendationsListEl, recommendations);

    if (euObligations) setList(euObligations, data.eu_obligations || []);
    if (euControls) setList(euControls, data.eu_controls || []);
    if (euRegulatoryObligations) setList(euRegulatoryObligations, data.eu_regulatory_obligations || []);
    if (euArticles) safeSet(euArticles, data.eu_articles || "—");

    safeSet(rawOutputEl, JSON.stringify(data, null, 2));
    safeSet(statusLine, "Analisi completata.");

  } catch (error) {
    setDecisionUI("HIGH", "Errore durante l'analisi");
    safeSet(riskLevelEl, "ERROR");
    safeSet(riskScoreEl, "—");
    safeSet(whyEl, "Non è stato possibile interpretare correttamente la richiesta.");
    safeSet(impactEl, "Analisi interrotta per errore backend o di rete.");
    safeSet(summaryEl, "Non è stato possibile ottenere una risposta valida dal backend.");
    safeSet(euClassificationEl, "—");
    safeHtml(gapsListEl, "<li>Controlla endpoint, CORS o risposta API.</li>");
    safeHtml(recommendationsListEl, "<li>Verifica che /analyze sia attivo e raggiungibile.</li>");
    safeSet(rawOutputEl, String(error));
    safeSet(statusLine, "Errore: " + error.message);

  } finally {
    analyzeBtn.disabled = false;
    clearBtn.disabled = false;
    pdfBtn.disabled = false;
  }
}

/* ── Export PDF ───────────────────────────────────────────── */

async function exportPdf() {
  const text = inputEl.value.trim();

  if (!text) {
    safeSet(statusLine, "Inserisci una descrizione prima di esportare il PDF.");
    inputEl.focus();
    return;
  }

  pdfBtn.disabled = true;
  analyzeBtn.disabled = true;
  clearBtn.disabled = true;
  safeSet(statusLine, "Generazione PDF executive in corso…");

  try {
    const response = await fetch(PDF_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "CL-qen-2026-xK9mPvZ3nRwQ7tYbDjF"
      },
      body: JSON.stringify({ system: text, context: "EU" })
    });

    if (!response.ok) {
      throw new Error("Errore nella generazione del PDF");
    }

    const blob = await response.blob();
    const url  = window.URL.createObjectURL(blob);
    const a    = document.createElement("a");

    a.href     = url;
    a.download = "cognitive-logic-executive-report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    safeSet(statusLine, "PDF executive generato correttamente.");

  } catch (error) {
    safeSet(statusLine, "Errore PDF: " + error.message);

  } finally {
    pdfBtn.disabled = false;
    analyzeBtn.disabled = false;
    clearBtn.disabled = false;
  }
}

/* ── Event Listeners ──────────────────────────────────────── */

analyzeBtn.addEventListener("click", sendMessage);

clearBtn.addEventListener("click", () => {
  inputEl.value = "";
  resetOutput();
  inputEl.focus();
});

pdfBtn.addEventListener("click", exportPdf);

inputEl.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    sendMessage();
  }
});

inputEl.addEventListener("input", () => {
  analyzeBtn.disabled = inputEl.value.trim() === "";
});

analyzeBtn.disabled = inputEl.value.trim() === "";
resetOutput();
