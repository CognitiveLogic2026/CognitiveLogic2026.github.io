"use strict";

document.addEventListener("DOMContentLoaded", async () => {
  const root = document.querySelector("[data-knowledge-graph]");

  if (!root) {
    return;
  }

  const nodesContainer = root.querySelector("[data-graph-nodes]");
  const details = root.querySelector("[data-graph-details]");
  const filter = root.querySelector("[data-graph-filter]");
  const reset = root.querySelector("[data-graph-reset]");

  if (!nodesContainer || !details || !filter || !reset) {
    console.error("Knowledge Graph: interfaccia incompleta.");
    return;
  }

  let graph;

  try {
    const response = await fetch(
      "/resources/graph/data/knowledge-graph.json",
      { headers: { Accept: "application/json" } }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    graph = await response.json();
  } catch (error) {
    console.error("Knowledge Graph loading error:", error);
    nodesContainer.innerHTML =
      "<p>Il Knowledge Graph non è disponibile.</p>";
    return;
  }

  const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
  const links = Array.isArray(graph.links) ? graph.links : [];

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const types = [...new Set(nodes.map((node) => node.type))].sort();

  for (const type of types) {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    filter.appendChild(option);
  }

  const relationsFor = (nodeId) =>
    links
      .filter(
        (link) =>
          link.source === nodeId ||
          link.target === nodeId
      )
      .map((link) => {
        const outgoing = link.source === nodeId;
        const relatedId = outgoing
          ? link.target
          : link.source;

        const relatedNode = nodes.find(
          (node) => node.id === relatedId
        );

        return {
          direction: outgoing ? "outgoing" : "incoming",
          relation: link.relation,
          node: relatedNode
        };
      })
      .filter((item) => item.node);

  const showDetails = (node) => {
    const relations = relationsFor(node.id);

    const relationMarkup = relations.length
      ? relations
          .map(
            (item) => `
              <li>
                <span>${escapeHtml(item.relation)}</span>
                <a href="${escapeHtml(item.node.url)}">
                  ${escapeHtml(item.node.title)}
                </a>
              </li>
            `
          )
          .join("")
      : "<li>Nessuna relazione disponibile.</li>";

    details.innerHTML = `
      <p class="graph-node-type">
        ${escapeHtml(node.type)}
      </p>

      <h2>${escapeHtml(node.title)}</h2>

      <p>
        Nodo appartenente all’architettura informativa
        e di governance Cognitive Logic.
      </p>

      <h3>Relazioni</h3>

      <ul class="graph-relation-list">
        ${relationMarkup}
      </ul>

      <a class="btn btn-primary" href="${escapeHtml(node.url)}">
        Apri la risorsa
      </a>
    `;
  };

  const render = () => {
    const selectedType = filter.value;

    const visibleNodes = selectedType
      ? nodes.filter((node) => node.type === selectedType)
      : nodes;

    nodesContainer.innerHTML = visibleNodes
      .map(
        (node) => `
          <button
            type="button"
            class="graph-node"
            data-node-id="${escapeHtml(node.id)}"
          >
            <span class="graph-node-type">
              ${escapeHtml(node.type)}
            </span>

            <strong>
              ${escapeHtml(node.title)}
            </strong>

            <span>
              ${relationsFor(node.id).length} relazioni
            </span>
          </button>
        `
      )
      .join("");

    for (const button of nodesContainer.querySelectorAll(
      "[data-node-id]"
    )) {
      button.addEventListener("click", () => {
        const node = nodes.find(
          (item) => item.id === button.dataset.nodeId
        );

        if (node) {
          showDetails(node);
        }
      });
    }
  };

  filter.addEventListener("change", render);

  reset.addEventListener("click", () => {
    filter.value = "";
    render();

    details.innerHTML = `
      <h2>Esplora il Knowledge Graph</h2>
      <p>
        Seleziona un nodo per visualizzare relazioni
        e risorse collegate.
      </p>
    `;
  });

  render();
});
