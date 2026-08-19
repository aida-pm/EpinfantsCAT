---
layout: page
title: Grip
image: /assets/images/plots/grip-titol.png
nav-menu: true
tile_color: grip
---

<div id="main" class="alt">

<section id="one">
    <div class="inner">

        <header class="major">
            <h1>Grip</h1>
        </header>

        <p>
            Evolució de la grip a partir de la vigilància sindròmica
            d'Atenció Primària i de la vigilància microbiològica
            sentinella.
        </p>


        <!-- ========================================================= -->
        <!-- SINDRÒMICA                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància sindròmica</h2>
        </header>

        <p>
            Incidència de la síndrome gripal per grup d'edat i total.
            Les dades sindròmiques són diàries i es representen amb
            una mitjana mòbil de 7 dies.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/grip-inc-ages.html' | relative_url }}"
                title="Incidència de grip per grup d'edat"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 450px;">
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
                src="{{ '/assets/interactive/grip-ontop.html' | relative_url }}"
                title="Incidència de grip per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 1000px;">
            </iframe>
        </div>


        <!-- ========================================================= -->
        <!-- MULTITESTS                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància microbiològica — multitests</h2>
        </header>

        <p>
            Incidència de proves positives de grip i percentatge de
            positivitat, per grup d'edat i total. Les dades dels
            multitests són setmanals i es representen sense
            suavitzar.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/grip-mt-ages.html' | relative_url }}"
                title="Multitests positius per influenza per grup d'edat"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 450px;">
            </iframe>
        </div>


        <!-- ========================================================= -->
        <!-- MULTITESTS — TEMPORADES                                   -->
        <!-- ========================================================= -->

        <header class="major">
            <h3>Comparació de temporades</h3>
        </header>

        <p>
            Comparació de les temporades de grip des de 2020 amb la
            temporada prepandèmica mitjana. Es mostren la incidència
            de proves positives i la positivitat sobre el mateix eix
            setembre-agost.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/grip-mt-ontop.html' | relative_url }}"
                title="Multitests positius per influenza per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 1000px;">
            </iframe>
        </div>

    </div>
</section>

</div>