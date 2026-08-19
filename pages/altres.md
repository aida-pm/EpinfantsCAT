---
layout: page
title: Altres
image: /assets/images/plots/altres-titol.png
nav-menu: true
tile_color: altres
---

<div id="main" class="alt">

<section id="one">
    <div class="inner">

        <header class="major">
            <h1>Altres</h1>
        </header>

        <p>
            Evolució d'altres virus i síndromes reportats a SIVIC que
            no corresponen a grip, VRS o COVID-19.
        </p>


        <!-- ========================================================= -->
        <!-- SINDRÒMICA                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància sindròmica</h2>
        </header>

        <p>
            Incidència de les diferents síndromes i diagnòstics per
            grup d'edat i total. Selecciona el diagnòstic que vols
            consultar mitjançant el menú.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/altres-inc-ages.html' | relative_url }}"
                title="Altres — incidència sindròmica per grup d'edat"
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
            el mateix eix setembre-agost. Selecciona el diagnòstic
            que vols consultar mitjançant el menú.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/altres-ontop.html' | relative_url }}"
                title="Altres — incidència sindròmica per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 450px;">
            </iframe>
        </div>


        <!-- ========================================================= -->
        <!-- MULTITESTS                                                -->
        <!-- ========================================================= -->

        <header class="major">
            <h2>Vigilància microbiològica — multitests</h2>
        </header>

        <p>
            Incidència de proves positives i percentatge de positivitat
            per als virus seleccionats, per grup d'edat i total.
            Les dades dels multitests són setmanals i es representen
            sense suavització. Selecciona el virus que vols consultar
            mitjançant el menú.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/altres-mt-ages.html' | relative_url }}"
                title="Altres — multitests per grup d'edat"
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
            Comparació de les temporades de les diferents infeccions
            des de 2020 amb la temporada prepandèmica mitjana. Cada
            temporada es representa sobre el mateix eix setembre-agost.
            Selecciona el virus que vols consultar mitjançant el menú.
        </p>

        <div class="iframe-container">
            <iframe
                src="{{ '/assets/interactive/altres-mt-ontop.html' | relative_url }}"
                title="Altres — multitests per temporada"
                loading="lazy"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: 450px;">
            </iframe>
        </div>

    </div>
</section>

</div>