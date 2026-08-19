---
layout: page
title: COVID-19
image: /assets/images/plots/covid19-titol.png
nav-menu: true
tile_color: covid19
---

<div id="main" class="alt">

<section id="one">
    <div class="inner">

        <header class="major">
            <h1>COVID-19</h1>
        </header>

        <p>
            Evolució del SARS-CoV-2 i de la COVID-19 a partir de la
            vigilància sindròmica i de la vigilància microbiològica
            sentinella.
        </p>


        <!-- ========================================================= -->
        <!-- SINDRÒMICA                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància sindròmica</h2>
        </header>

        <p>
            Incidència dels diagnòstics relacionats amb la COVID-19 per
            grup d'edat i total. Les dades sindròmiques són diàries i
            es representen amb una mitjana mòbil de 7 dies.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/covid19-inc-ages.html' | relative_url }}"
                title="COVID-19 — incidència sindròmica per grup d'edat"
                loading="lazy"
                frameborder="0"
                allowfullscreen>
            </iframe>
        </div>


        <!-- ========================================================= -->
        <!-- SINDRÒMICA — TEMPORADES                                   -->
        <!-- ========================================================= -->

        <header class="major">
            <h3>Comparació de temporades</h3>
        </header>

        <p>
            Comparació de les temporades des de 2020 amb la temporada
            prepandèmica mitjana. Cada temporada es representa sobre
            el mateix eix setembre-agost.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/covid19-ontop.html' | relative_url }}"
                title="COVID-19 — incidència sindròmica per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen>
            </iframe>
        </div>


        <!-- ========================================================= -->
        <!-- MULTITESTS                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància microbiològica — multitests</h2>
        </header>

        <p>
            Incidència de proves positives de SARS-CoV-2 i percentatge
            de positivitat, per grup d'edat i total. Les dades dels
            multitests són setmanals i es representen sense
            suavització.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/covid19-mt-ages.html' | relative_url }}"
                title="COVID-19 — multitests per grup d'edat"
                loading="lazy"
                frameborder="0"
                allowfullscreen>
            </iframe>
        </div>


        <!-- ========================================================= -->
        <!-- MULTITESTS — TEMPORADES                                   -->
        <!-- ========================================================= -->

        <header class="major">
            <h3>Comparació de temporades</h3>
        </header>

        <p>
            Comparació de les temporades de SARS-CoV-2 des de 2020 amb
            la temporada prepandèmica mitjana. Es mostren la incidència
            de proves positives i la positivitat sobre el mateix eix
            setembre-agost.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/covid19-mt-ontop.html' | relative_url }}"
                title="COVID-19 — multitests per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen>
            </iframe>
        </div>

    </div>
</section>

</div>