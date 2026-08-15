---
layout: home
title: Home
landing-title: 'EpinfantsCAT'
description: 'Vigilància epidemiològica d''infeccions pediàtriques a Catalunya.'
image: null
author: null
show_tile: false
---

EpinfantsCAT recull i visualitza dades públiques de vigilància epidemiològica pediàtrica a Catalunya, combinant la vigilància sindròmica d'infeccions a Atenció Primària amb la vigilància microbiològica sentinella. Les figures de sota s'actualitzen a partir de les dades obertes de la Generalitat de Catalunya.

<!--
  PLOTS GALLERY
  --------------
  Loops over the `plots` collection (configured in _config.yml) and shows
  each figure as a clickable thumbnail linking to its own page. Sorted
  newest first. Regenerated automatically by scripts/generate_site_plots.py.
-->

<section id="plots-gallery" style="padding: 2rem 0;">
  <h2 style="text-align:center; margin-bottom: 2rem;">Figures</h2>

  <div class="plots-grid" style="
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1.5rem;
      max-width: 1100px;
      margin: 0 auto;
  ">
    {% assign sorted_plots = site.plots | sort: "date" | reverse %}
    {% for plot in sorted_plots %}
      <a href="{{ plot.url | relative_url }}" class="plot-card" style="
          display: block;
          text-decoration: none;
          color: inherit;
          border: 1px solid #e5e5e5;
          border-radius: 8px;
          overflow: hidden;
          transition: box-shadow 0.2s ease, transform 0.2s ease;
      "
      onmouseover="this.style.boxShadow='0 6px 18px rgba(0,0,0,0.12)'; this.style.transform='translateY(-3px)';"
      onmouseout="this.style.boxShadow='none'; this.style.transform='translateY(0)';"
      >
        <img src="{{ plot.image | relative_url }}" alt="{{ plot.title }}"
             style="width: 100%; height: 180px; object-fit: cover; display: block;">
        <div style="padding: 0.9rem 1rem;">
          <h3 style="margin: 0 0 0.3rem 0; font-size: 1.05rem;">{{ plot.title }}</h3>
          <p style="margin: 0; font-size: 0.85rem; color: #777;">{{ plot.date | date: "%d %B %Y" }}</p>
        </div>
      </a>
    {% endfor %}
  </div>

  {% if site.plots.size == 0 %}
    <p style="text-align:center; color:#999;">Encara no hi ha figures generades — executa scripts/generate_site_plots.py.</p>
  {% endif %}
</section>
