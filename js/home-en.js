    fetch('/data/fuorimenu.json')
      .then(r => r.json())
      .then(d => {
        const feed = document.getElementById('fuorimenu-feed');
        feed.innerHTML = d.articoli.map(a => `
          <div class="ed">
            <div class="ed-tag">${a.tag} · ${a.data}</div>
            <div class="ed-title">${a.titolo}</div>
            <div class="ed-quote">${a.estratto}</div>
            <div class="ed-meta">
              <span>Roberto Bob Malini · Fuorimenu</span>
              <a href="${a.url}" target="_blank" rel="noopener">→ Read on Substack</a>
            </div>
          </div>
        `).join('');
      })
      .catch(() => {
        document.getElementById('fuorimenu-feed').innerHTML =
          '<div class="ed"><div class="ed-title">Fuorimenu — <a href="https://fuorimenu.substack.com" target="_blank">fuorimenu.substack.com</a></div></div>';
      });
