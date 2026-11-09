/* ═══════════════════════════════════════════════════════════════════════
   U-Work — Tema claro / oscuro
   Un solo lugar decide como se cambia de tema. Antes cada pantalla
   tenía su propia copia: las que heredan de base.html una version, login
   otra, la seleccion de rol otra y la verificacion de correo ninguna.
   El resultado era que el interruptor no aparecia en unas pantallas y en
   otras el icono no se actualizaba al cambiar.
   ═══════════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    function esOscuro() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    }

    function alternar() {
        if (esOscuro()) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('uwork-theme', 'light');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('uwork-theme', 'dark');
        }
        pintar();
    }

    function pintar() {
        var oscuro = esOscuro();
        document.querySelectorAll(
            '.theme-toggle-btn i, .sidebar-theme-toggle i, .theme-toggle-float i'
        ).forEach(function (icono) {
            icono.className = oscuro ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        });

        // La etiqueta del interruptor de la barra lateral dice a que tema
        // se pasa, no en el que se esta.
        var etiqueta = document.querySelector('.sidebar-theme-toggle span');
        if (etiqueta) {
            etiqueta.textContent = oscuro ? 'Tema claro' : 'Tema oscuro';
        }

        // El flotante dice lo mismo en su nombre accesible, para que el
        // lector de pantalla anuncie la accion y no el estado.
        document.querySelectorAll('.theme-toggle-float').forEach(function (boton) {
            var texto = oscuro ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro';
            boton.setAttribute('aria-label', texto);
            boton.setAttribute('title', texto);
        });
    }

    function iniciar() {
        document.querySelectorAll('[data-theme-toggle]').forEach(function (boton) {
            boton.addEventListener('click', alternar);
        });
        pintar();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();
