---
layout: page
title: VRS
image: /assets/images/plots/virus-vrs.png
nav-menu: true
---

<div id="main" class="alt">
<section id="one">
	<div class="inner">
		<header class="major">
			<h1>VRS</h1>
		</header>
		<p>Totes les figures relacionades amb el virus respiratori sincitial (VRS), principal causant de bronquiolitis en infants.</p>

		<div class="plots-grid" style="
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
			gap: 1.5rem;
			margin-top: 2rem;
		">
			{% assign category_plots = site.plots | where: "category", "vrs" | sort: "date" | reverse %}
			{% for plot in category_plots %}
			<a href="{{ plot.url | relative_url }}" class="plot-card" style="
					display: block;
					text-decoration: none;
					color: inherit;
					border: 1px solid #e5e5e5;
					border-radius: 8px;
					overflow: hidden;
			">
				<img src="{{ plot.image | relative_url }}" alt="{{ plot.title }}"
						 style="width: 100%; height: 180px; object-fit: cover; display: block;">
				<div style="padding: 0.9rem 1rem;">
					<h3 style="margin: 0 0 0.3rem 0; font-size: 1.05rem;">{{ plot.title }}</h3>
				</div>
			</a>
			{% endfor %}
		</div>

		{% if category_plots.size == 0 %}
			<p>Encara no hi ha figures de VRS generades.</p>
		{% endif %}
	</div>
</section>
</div>
