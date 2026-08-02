"use strict";

document.addEventListener("DOMContentLoaded", async () => {
  const root = document.querySelector("[data-resource-search]");

  if (!root) {
    return;
  }

  const input = root.querySelector("[data-resource-query]");
  const typeFilter = root.querySelector("[data-resource-type]");
  const categoryFilter = root.querySelector("[data-resource-category]");
  const sortFilter = root.querySelector("[data-resource-sort]");
  const featuredOnly = root.querySelector("[data-resource-featured]");
  const results = root.querySelector("[data-resource-results]");
  const count = root.querySelector("[data-resource-count]");
  const empty = root.querySelector("[data-resource-empty]");
  const reset = root.querySelector("[data-resource-reset]");

  if (
    !input ||
    !typeFilter ||
    !categoryFilter ||
    !sortFilter ||
    !featuredOnly ||
    !results ||
    !count ||
    !empty ||
    !reset
  ) {
    console.error("Resource search: required interface elements are missing.");
    return;
  }

  let resources = [];

  try {
    const response = await fetch("/resources/data/resources.json", {
      headers: {
        Accept: "application/json"
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();

    if (!Array.isArray(payload)) {
      throw new Error("Invalid catalogue format");
    }

    resources = payload.filter(
      (item) => item && item.status === "published"
    );
  } catch (error) {
    console.error("Resource catalogue loading failed:", error);

    results.innerHTML = `
      <p class="resource-search-error">
        Il catalogo non è disponibile in questo momento.
      </p>
    `;

    count.textContent = "0 risorse";
    return;
  }

  const normalize = (value) =>
    String(value ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();

  const categoryLabels = {
    publications: "Publications",
    research: "Research",
    "validation-case-studies": "Validation e Case Studies",
    "executive-guides": "Executive Guides"
  };

  const uniqueSorted = (values) =>
    [...new Set(values.filter(Boolean))].sort((a, b) =>
      String(a).localeCompare(String(b), "it", {
        sensitivity: "base"
      })
    );

  const populateSelect = (select, values, labels = {}) => {
    for (const value of values) {
      const option = document.createElement("option");

      option.value = value;
      option.textContent = labels[value] || value;

      select.appendChild(option);
    }
  };

  populateSelect(
    typeFilter,
    uniqueSorted(resources.map((item) => item.type))
  );

  populateSelect(
    categoryFilter,
    uniqueSorted(resources.map((item) => item.category)),
    categoryLabels
  );

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const createCard = (item) => {
    const topics = Array.isArray(item.topics) ? item.topics : [];

    const topicMarkup = topics
      .map(
        (topic) =>
          `<span class="resource-topic">${escapeHtml(topic)}</span>`
      )
      .join("");

    const featuredMarkup = item.featured
      ? '<span class="resource-badge resource-badge--featured">In evidenza</span>'
      : "";

    return `
      <a class="resource-result-card" href="${escapeHtml(item.url)}">
        <div class="resource-result-meta">
          <span class="resource-badge">${escapeHtml(item.type)}</span>
          ${featuredMarkup}
        </div>

        <h2 class="notranslate" translate="no">${escapeHtml(item.title)}</h2>

        <p>
          ${escapeHtml(item.description)}
        </p>

        <div class="resource-topic-list">
          ${topicMarkup}
        </div>

        <span class="resource-result-link">Apri documento →</span>
      </a>
    `;
  };

  const setCount = (selector, value) => {
    const element = document.querySelector(selector);
    if (element) element.textContent = String(value);
  };
  setCount("[data-count-total]", resources.length);
  setCount("[data-count-categories]", new Set(resources.map((item) => item.category)).size);
  setCount("[data-count-research]", resources.filter((item) => item.category === "research").length);
  setCount("[data-count-watch]", resources.filter((item) => item.category === "international-watch").length);
  setCount("[data-count-validation]", resources.filter((item) => item.category === "validation-case-studies").length);

  const getSearchText = (item) =>
    normalize(
      [
        item.title,
        item.description,
        item.type,
        item.category,
        item.audience,
        ...(Array.isArray(item.topics) ? item.topics : [])
      ].join(" ")
    );

  const applyFilters = () => {
    const query = normalize(input.value);
    const selectedType = typeFilter.value;
    const selectedCategory = categoryFilter.value;
    const selectedSort = sortFilter.value;
    const requireFeatured = featuredOnly.checked;

    let filtered = resources.filter((item) => {
      if (query && !getSearchText(item).includes(query)) {
        return false;
      }

      if (selectedType && item.type !== selectedType) {
        return false;
      }

      if (
        selectedCategory &&
        item.category !== selectedCategory
      ) {
        return false;
      }

      if (requireFeatured && !item.featured) {
        return false;
      }

      return true;
    });

    filtered = filtered.sort((a, b) => {
      if (selectedSort === "featured") {
        if (a.featured !== b.featured) {
          return Number(b.featured) - Number(a.featured);
        }
      }

      if (selectedSort === "type") {
        const typeComparison = String(a.type).localeCompare(
          String(b.type),
          "it",
          { sensitivity: "base" }
        );

        if (typeComparison !== 0) {
          return typeComparison;
        }
      }

      return String(a.title).localeCompare(
        String(b.title),
        "it",
        { sensitivity: "base" }
      );
    });

    results.innerHTML = filtered.map(createCard).join("");

    const total = filtered.length;

    count.textContent =
      total === 1 ? "1 risorsa" : `${total} risorse`;

    empty.hidden = total !== 0;
  };

  const resetFilters = () => {
    input.value = "";
    typeFilter.value = "";
    categoryFilter.value = "";
    sortFilter.value = "featured";
    featuredOnly.checked = false;

    applyFilters();
    input.focus();
  };

  input.addEventListener("input", applyFilters);
  typeFilter.addEventListener("change", applyFilters);
  categoryFilter.addEventListener("change", applyFilters);
  sortFilter.addEventListener("change", applyFilters);
  featuredOnly.addEventListener("change", applyFilters);
  reset.addEventListener("click", resetFilters);

  applyFilters();
});
