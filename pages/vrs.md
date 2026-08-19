---
layout: page
title: VRS
image: /assets/images/plots/vrs-titol.png
nav-menu: true
tile_color: vrs
---

<div id="main" class="alt">

<section id="one">
    <div class="inner">

        <header class="major">
            <h1>VRS</h1>
        </header>

        <p>
            Evolució del virus respiratori sincitial (VRS), principal
            causant de bronquiolitis en infants.
        </p>


        <!-- ========================================================= -->
        <!-- SINDRÒMICA                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància sindròmica</h2>
        </header>

        <p>
            Incidència de bronquiolitis per grup
            d'edat i total. Les dades sindròmiques són diàries i es
            representen amb una mitjana mòbil de 7 dies.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/vrs-inc-ages.html' | relative_url }}"
                title="Incidència de bronquiolitis per grup d'edat"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 450px;">
            </iframe>
        </div>

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
                src="{{ '/assets/interactive/vrs-ontop.html' | relative_url }}"
                title="Incidència de bronquiolitis per temporada"
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
            Incidència de proves positives per VRS i percentatge de
            positivitat, per grup d'edat i total. Les dades dels
            multitests són setmanals i es representen sense suavitzar.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/vrs-mt-ages.html' | relative_url }}"
                title="Multitests positius per VRS per grup d'edat"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 450px;">
            </iframe>
        </div>

        <header class="major">
            <h3>Comparació de temporades</h3>
        </header>

        <p>
            Comparació de les temporades de VRS des de 2020 amb la
            temporada prepandèmica mitjana. Es mostren la incidència
            de proves positives i la positivitat sobre el mateix eix
            setembre-agost.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/vrs-mt-ontop.html' | relative_url }}"
                title="Multitests positius per VRS per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 1000px;">
            </iframe>
        </div>

    </div>
</section>

</div>