/* ═══════════════════════════════════════════════════════════════════════
   U-Work — Interacción de formularios
   Un solo archivo para los tres patrones que comparten los formularios
   largos de la aplicacion:

   1. Asistente por pasos (registro de estudiante, registro de empleador,
      publicacion de un trabajo).
   2. Validación en vivo con mensajes en español y foco al primer error.
   3. Controles con estado: medidor de contraseña, entrada de etiquetas,
      vista previa de archivo y contador de caracteres.

   No hay manejadores inline: la CSP los bloquea, asi que todo se registra
   con addEventListener. Tampoco hay listeners de scroll: el avance del
   asistente depende de la acción del usuario, no de la posicion.
   ═══════════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    var REDUCIDO = window.matchMedia
        ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
        : false;

    /* ---------------------------------------------------------------
       Utilidades
       --------------------------------------------------------------- */

    function todos(raiz, selector) {
        return Array.prototype.slice.call(raiz.querySelectorAll(selector));
    }

    function wrapperDeCampo(campo) {
        return campo.closest ? campo.closest('.field') : null;
    }

    /* Busca dentro del propio campo el elemento que acompaña al control
       (medidor, contador, valor en pesos). Los atributos viajan en el
       HTML desde el servidor, asi que no hay dependencia del orden en
       que se cargan los scripts. */
    function acompanante(campo, selector) {
        var wrapper = wrapperDeCampo(campo);
        return wrapper ? wrapper.querySelector(selector) : null;
    }

    function mensajeDeError(campo) {
        if (!campo || campo.disabled) return null;
        if (campo.type === 'file') {
            if (campo.required && (!campo.files || !campo.files.length)) {
                return 'Adjunta un archivo para continuar.';
            }
            return null;
        }
        if (campo.type === 'checkbox' || campo.type === 'radio') {
            if (campo.required && !campo.checked) {
                return 'Debes marcar esta casilla para continuar.';
            }
            return null;
        }
        var valor = (campo.value || '').trim();
        if (campo.required && !valor) return 'Este campo es obligatorio.';
        if (!valor) return null;
        if (campo.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
            return 'Escribe un correo electrónico válido.';
        }
        if (campo.type === 'url') {
            try {
                new URL(valor);
            } catch (e) {
                return 'Escribe una dirección web válida.';
            }
        }
        if (campo.minLength > 0 && valor.length < campo.minLength) {
            return 'Debe tener al menos ' + campo.minLength + ' caracteres.';
        }
        if (campo.type === 'number') {
            if (campo.min !== '' && campo.min !== undefined &&
                parseFloat(valor) < parseFloat(campo.min)) {
                return 'El valor no puede ser menor que ' + campo.min + '.';
            }
            if (campo.max !== '' && campo.max !== undefined &&
                parseFloat(valor) > parseFloat(campo.max)) {
                return 'El valor no puede ser mayor que ' + campo.max + '.';
            }
        }
        return null;
    }

    function limpiarError(campo) {
        if (!campo) return;
        // El aviso de confirmacion de contrasena tiene su propio ciclo de
        // vida: si esta activo, manda el y el campo sigue marcado como
        // invalido.
        if (campo.getAttribute('data-confirmacion')) return;
        campo.removeAttribute('aria-invalid');
        campo.classList.remove('is-invalid');
        var wrapper = wrapperDeCampo(campo);
        if (!wrapper) return;
        var previo = wrapper.querySelector('[data-error-propio]');
        if (previo) previo.remove();
        var servidor = wrapper.querySelector('.field__error[data-error-servidor]');
        // Un error que vino del servidor no se borra por teclear: se
        // reemplaza cuando el campo vuelve a ser valido.
        if (servidor) {
            servidor.remove();
            if (campo.getAttribute('aria-describedby')) {
                campo.removeAttribute('aria-describedby');
            }
        }
    }

    function mostrarError(campo, mensaje) {
        if (!campo) return;
        var wrapper = wrapperDeCampo(campo);
        if (!wrapper) return;

        var previo = wrapper.querySelector('[data-error-propio]');
        if (previo) previo.remove();
        var servidor = wrapper.querySelector('[data-error-servidor]');
        if (servidor) servidor.remove();
        // Un error general reemplaza al aviso de confirmacion: los dos a
        // la vez dicen lo mismo y ocupan dos veces.
        var confirmacion = wrapper.querySelector('[data-error-contrasena]');
        if (confirmacion) confirmacion.remove();
        campo.removeAttribute('data-confirmacion');

        var caja = document.createElement('div');
        caja.className = 'field__error';
        caja.setAttribute('role', 'alert');
        caja.setAttribute('data-error-propio', '');
        caja.id = campo.id + '-error';

        var icono = document.createElement('i');
        icono.className = 'bi bi-exclamation-circle';
        icono.setAttribute('aria-hidden', 'true');

        var texto = document.createElement('span');
        texto.textContent = mensaje;

        caja.appendChild(icono);
        caja.appendChild(texto);
        wrapper.appendChild(caja);

        campo.setAttribute('aria-invalid', 'true');
        campo.setAttribute('aria-describedby', caja.id);
        campo.classList.add('is-invalid');
    }

    function validarCampo(campo) {
        var mensaje = mensajeDeError(campo);
        if (mensaje) {
            mostrarError(campo, mensaje);
            return false;
        }
        limpiarError(campo);
        return true;
    }

    function validarContenedor(contenedor) {
        var campos = todos(contenedor, 'input, select, textarea')
            .filter(function (campo) {
                return campo.type !== 'hidden' && !campo.disabled;
            });
        var primerFallo = null;
        campos.forEach(function (campo) {
            if (!validarCampo(campo) && !primerFallo) primerFallo = campo;
        });
        return { ok: !primerFallo, campo: primerFallo };
    }

    /* ---------------------------------------------------------------
       1. Asistente por pasos
       --------------------------------------------------------------- */

    function iniciarAsistente(formulario) {
        var paneles = todos(formulario, '[data-step-panel]');
        if (paneles.length < 2) return;

        var botones = todos(formulario, '[data-step-target]');
        var meta = formulario.querySelector('[data-step-meta]');
        var titulos = {};
        todos(formulario, '[data-step-title]').forEach(function (el) {
            titulos[el.getAttribute('data-step-title')] = el.textContent.trim();
        });

        var actual = 1;
        var maxAlcanzado = 1;

        function panelDe(numero) {
            return paneles.filter(function (p) {
                return p.getAttribute('data-step-panel') === String(numero);
            })[0];
        }

        function indiceDe(panel) {
            return paneles.indexOf(panel) + 1;
        }

        function mostrar(numero, enfocar) {
            actual = numero;
            if (numero > maxAlcanzado) maxAlcanzado = numero;

            paneles.forEach(function (panel) {
                var esActivo = indiceDe(panel) === numero;
                panel.classList.toggle('is-active', esActivo);
                if (esActivo) {
                    panel.removeAttribute('hidden');
                } else {
                    panel.setAttribute('hidden', '');
                }
            });

            botones.forEach(function (boton) {
                var destino = parseInt(boton.getAttribute('data-step-target'), 10);
                var item = boton.closest('.stepper__item');
                if (!item) return;
                item.classList.toggle('is-current', destino === numero);
                item.classList.toggle('is-done', destino < numero);
                boton.setAttribute('aria-current', destino === numero ? 'step' : 'false');
            });

            if (meta) {
                var nombre = titulos[String(numero)] || '';
                meta.innerHTML = '';
                var paso = document.createElement('span');
                paso.className = 'tnum';
                paso.textContent = 'Paso ' + numero + ' de ' + paneles.length;
                meta.appendChild(paso);
                if (nombre) {
                    var sep = document.createElement('span');
                    sep.setAttribute('aria-hidden', 'true');
                    sep.textContent = '·';
                    var etiqueta = document.createElement('strong');
                    etiqueta.textContent = nombre;
                    meta.appendChild(sep);
                    meta.appendChild(etiqueta);
                }
            }

            var panel = panelDe(numero);
            if (panel) {
                var cabecera = panel.querySelector('[data-step-heading]');
                if (cabecera) {
                    cabecera.setAttribute('tabindex', '-1');
                    // En el primer render no se enfoca nada: el usuario
                    // acaba de llegar a la pagina y el foco debe quedarse
                    // donde estaba.
                    if (enfocar !== false) {
                        cabecera.focus({ preventScroll: true });
                    }
                }
                if (enfocar !== false) {
                    panel.scrollIntoView({
                        behavior: REDUCIDO ? 'auto' : 'smooth',
                        block: 'nearest'
                    });
                }
            }
        }

        // Los botones de atras y siguiente viven dentro de cada panel.
        todos(formulario, '[data-step-next]').forEach(function (boton) {
            boton.addEventListener('click', function () {
                var panel = boton.closest('[data-step-panel]');
                if (!panel) return;
                var resultado = validarContenedor(panel);
                if (!resultado.ok) {
                    resultado.campo.focus();
                    return;
                }
                var siguiente = indiceDe(panel) + 1;
                if (siguiente <= paneles.length) mostrar(siguiente);
            });
        });

        todos(formulario, '[data-step-back]').forEach(function (boton) {
            boton.addEventListener('click', function () {
                var panel = boton.closest('[data-step-panel]');
                if (!panel) return;
                var anterior = indiceDe(panel) - 1;
                if (anterior >= 1) mostrar(anterior);
            });
        });

        // El indicador superior es navegable. Hacia atras siempre se
        // puede ir. Hacia adelante se valida el paso actual: si esta
        // completo se salta, y si le falta algo el foco va al campo.
        // Los botones nunca se deshabilitan: un boton deshabilitado no es
        // alcanzable con el teclado.
        botones.forEach(function (boton) {
            boton.addEventListener('click', function () {
                var destino = parseInt(boton.getAttribute('data-step-target'), 10);
                if (destino === actual) return;
                if (destino < actual) {
                    mostrar(destino);
                    return;
                }
                var panel = panelDe(actual);
                var resultado = validarContenedor(panel);
                if (!resultado.ok) {
                    resultado.campo.focus();
                    return;
                }
                mostrar(destino);
            });
        });

        // Al enviar se revisa el paso visible. Si algo falla se corrige
        // ahi mismo en vez de dejar al usuario en un paso equivocado.
        formulario.addEventListener('submit', function (evento) {
            var panel = panelDe(actual);
            if (!panel) return;
            var resultado = validarContenedor(panel);
            if (!resultado.ok) {
                evento.preventDefault();
                resultado.campo.focus();
                return;
            }
            var boton = formulario.querySelector('[data-submit-btn]');
            if (boton) {
                boton.disabled = true;
                var etiqueta = boton.querySelector('[data-submit-label]');
                if (etiqueta) etiqueta.textContent = boton.getAttribute('data-submit-pending') || 'Enviando...';
            }
        });

        // El resumen de errores enlaza a cada campo. Al pulsarlo se abre
        // el paso que lo contiene y el foco cae en el campo: sin esto el
        // enlace solo cambiaria el scroll de una pagina que ya no esta.
        todos(formulario, '[data-error-link]').forEach(function (enlace) {
            enlace.addEventListener('click', function (evento) {
                var idCampo = (enlace.getAttribute('href') || '').slice(1);
                var campo = document.getElementById(idCampo);
                if (!campo) return;
                evento.preventDefault();
                var panel = campo.closest('[data-step-panel]');
                if (panel) {
                    var indice = indiceDe(panel);
                    if (indice > maxAlcanzado) maxAlcanzado = indice;
                    mostrar(indice);
                }
                campo.focus();
            });
        });

        // Error del servidor: se abre el paso que lo contiene. Sin esto la
        // persona ve un formulario vacio y no entiende que paso falta.
        var conError = formulario.querySelector('[aria-invalid="true"]');
        if (conError) {
            var panelConError = conError.closest('[data-step-panel]');
            if (panelConError) {
                maxAlcanzado = indiceDe(panelConError);
                mostrar(maxAlcanzado);
                var foco = panelConError.querySelector('[aria-invalid="true"]');
                if (foco) foco.focus();
                return;
            }
        }

        mostrar(1, false);
    }

    /* ---------------------------------------------------------------
       2. Medidor de fortaleza de contraseña
       --------------------------------------------------------------- */

    function iniciarMedidor(campo) {
        var medidor = acompanante(campo, '[data-meter]');
        if (!medidor) return;

        var segmentos = todos(medidor, '[data-meter-seg]');
        var texto = medidor.querySelector('[data-meter-text]');
        var etiquetas = ['Muy corta', 'Débil', 'Aceptable', 'Buena', 'Segura'];
        var clases = ['is-on-weak', 'is-on-fair', 'is-on-good', 'is-on-strong'];

        function puntuar(valor) {
            if (!valor) return 0;
            var puntos = 0;
            if (valor.length >= 8) puntos++;
            if (valor.length >= 12) puntos++;
            if (/[a-z]/.test(valor) && /[A-Z]/.test(valor)) puntos++;
            if (/[0-9]/.test(valor)) puntos++;
            if (/[^A-Za-z0-9]/.test(valor)) puntos++;
            return Math.min(puntos, 4);
        }

        function pintar() {
            var puntos = puntuar(campo.value || '');
            segmentos.forEach(function (segmento, indice) {
                segmento.className = 'meter__seg';
                if (indice < puntos) {
                    segmento.classList.add(clases[Math.min(puntos, 4) - 1]);
                }
            });
            if (texto) texto.textContent = etiquetas[Math.min(puntos, 4)];
        }

        campo.addEventListener('input', pintar);
        pintar();
    }

    /* ---------------------------------------------------------------
       3. Confirmacion de contraseña
       --------------------------------------------------------------- */

    function iniciarConfirmacion(campo) {
        var origenId = campo.getAttribute('data-password-match');
        var origen = document.getElementById(origenId);
        if (!origen) return;
        var wrapper = wrapperDeCampo(campo);
        var aviso = null;

        function quitarAviso() {
            if (aviso) { aviso.remove(); aviso = null; }
            campo.removeAttribute('data-confirmacion');
            campo.removeAttribute('aria-invalid');
            campo.classList.remove('is-invalid');
        }

        function revisar() {
            if (!origen.value || origen.value === campo.value) {
                quitarAviso();
                return;
            }
            if (!aviso && wrapper) {
                aviso = document.createElement('div');
                aviso.className = 'field__error';
                aviso.setAttribute('role', 'alert');
                aviso.setAttribute('data-error-contrasena', '');
                var icono = document.createElement('i');
                icono.className = 'bi bi-exclamation-circle';
                icono.setAttribute('aria-hidden', 'true');
                var texto = document.createElement('span');
                texto.textContent = 'Las contraseñas no coinciden.';
                aviso.appendChild(icono);
                aviso.appendChild(texto);
                wrapper.appendChild(aviso);
            }
            campo.setAttribute('data-confirmacion', 'pendiente');
            campo.setAttribute('aria-invalid', 'true');
            campo.classList.add('is-invalid');
        }

        campo.addEventListener('input', revisar);
        origen.addEventListener('input', revisar);
    }

    /* ---------------------------------------------------------------
       4. Entrada de etiquetas (habilidades)
       --------------------------------------------------------------- */

    function iniciarEtiquetas(campo) {
        var wrapper = wrapperDeCampo(campo);
        if (!wrapper) return;
        var lista = wrapper.querySelector('[data-tag-list]');
        var entrada = wrapper.querySelector('[data-tag-entry]');
        if (!lista || !entrada) return;

        function valores() {
            return campo.value.split(',').map(function (v) {
                return v.trim();
            }).filter(function (v) {
                return v.length > 0;
            });
        }

        function sincronizar() {
            campo.value = valores().join(', ');
            lista.querySelectorAll('[data-tag]').forEach(function (chip) {
                chip.remove();
            });
            valores().forEach(function (valor) {
                var chip = document.createElement('span');
                chip.className = 'chip chip--brand';
                chip.setAttribute('data-tag', '');

                var texto = document.createElement('span');
                texto.textContent = valor;
                chip.appendChild(texto);

                var quitar = document.createElement('button');
                quitar.type = 'button';
                quitar.className = 'tag-remove';
                quitar.setAttribute('aria-label', 'Quitar ' + valor);
                quitar.innerHTML = '<i class="bi bi-x" aria-hidden="true"></i>';
                quitar.addEventListener('click', function () {
                    campo.value = valores().filter(function (v) {
                        return v !== valor;
                    }).join(', ');
                    sincronizar();
                });
                chip.appendChild(quitar);

                lista.appendChild(chip);
            });
            var vacio = lista.querySelector('[data-tag-empty]');
            if (vacio) vacio.hidden = valores().length > 0;
        }

        function agregar() {
            var texto = entrada.value.trim().replace(/,$/, '');
            if (!texto) return;
            var actuales = valores();
            if (actuales.indexOf(texto) === -1) actuales.push(texto);
            campo.value = actuales.join(', ');
            entrada.value = '';
            sincronizar();
        }

        entrada.addEventListener('keydown', function (evento) {
            if (evento.key === 'Enter' || evento.key === ',') {
                evento.preventDefault();
                agregar();
            } else if (evento.key === 'Backspace' && !entrada.value) {
                var actuales = valores();
                if (actuales.length) {
                    campo.value = actuales.slice(0, -1).join(', ');
                    sincronizar();
                }
            }
        });

        entrada.addEventListener('blur', agregar);
        campo.addEventListener('input', sincronizar);
        sincronizar();
    }

    /* ---------------------------------------------------------------
       5. Vista previa de archivo
       --------------------------------------------------------------- */

    function iniciarCarga(campo) {
        var zona = campo.closest('[data-upload-zone]');
        if (!zona) return;
        var preview = zona.querySelector('[data-upload-preview]');
        var nombre = zona.querySelector('[data-upload-name]');
        var meta = zona.querySelector('[data-upload-meta]');
        var icono = zona.querySelector('[data-upload-icon]');
        var error = zona.querySelector('[data-upload-error]');

        function tamano(archivo) {
            if (archivo.size < 1024) return archivo.size + ' B';
            if (archivo.size < 1024 * 1024) {
                return Math.round(archivo.size / 1024) + ' KB';
            }
            return (archivo.size / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function fallo(mensaje) {
            if (!error) return;
            error.textContent = mensaje || '';
            error.hidden = !mensaje;
        }

        campo.addEventListener('change', function () {
            var archivo = campo.files && campo.files[0];
            if (!archivo) {
                if (preview) preview.classList.remove('is-visible');
                fallo('');
                return;
            }
            if (archivo.type && archivo.type.indexOf('image/') !== 0) {
                fallo('El archivo debe ser una imagen JPG o PNG.');
                campo.value = '';
                if (preview) preview.classList.remove('is-visible');
                return;
            }
            if (archivo.size > 5 * 1024 * 1024) {
                fallo('La imagen supera el máximo de 5 MB.');
                campo.value = '';
                if (preview) preview.classList.remove('is-visible');
                return;
            }
            fallo('');
            if (nombre) nombre.textContent = archivo.name;
            if (meta) meta.textContent = tamano(archivo);
            if (icono) icono.className = 'bi bi-check-circle-fill';

            var lector = new FileReader();
            lector.onload = function (evento) {
                if (!preview) return;
                var imagen = preview.querySelector('img');
                if (imagen) imagen.src = evento.target.result;
                preview.classList.add('is-visible');
            };
            lector.readAsDataURL(archivo);
        });

        // Arrastrar y soltar. El control real sigue siendo el input: la
        // zona solo dispara el click.
        ['dragenter', 'dragover'].forEach(function (nombreEvento) {
            zona.addEventListener(nombreEvento, function (evento) {
                evento.preventDefault();
                zona.classList.add('is-drag');
            });
        });
        ['dragleave', 'drop'].forEach(function (nombreEvento) {
            zona.addEventListener(nombreEvento, function (evento) {
                evento.preventDefault();
                zona.classList.remove('is-drag');
            });
        });
        zona.addEventListener('drop', function (evento) {
            if (!campo.files || !evento.dataTransfer) return;
            if (evento.dataTransfer.files.length) {
                campo.files = evento.dataTransfer.files;
                campo.dispatchEvent(new Event('change'));
            }
        });
    }

    /* ---------------------------------------------------------------
       6. Contador de caracteres
       --------------------------------------------------------------- */

    function iniciarContador(caja) {
        // La caja del contador es lo que se marca en el HTML: el control
        // que cuenta es el primero dentro de su campo.
        var wrapper = wrapperDeCampo(caja);
        if (!wrapper) return;
        var campo = wrapper.querySelector('input, textarea, select');
        if (!campo) return;
        var maximo = parseInt(campo.getAttribute('maxlength'), 10);
        var salida = caja.querySelector('[data-counter-text]');

        function pintar() {
            var largo = (campo.value || '').length;
            if (salida) salida.textContent = isNaN(maximo) ? String(largo) : largo + ' / ' + maximo;
            caja.classList.toggle('is-over', !isNaN(maximo) && largo > maximo);
        }

        campo.addEventListener('input', pintar);
        pintar();
    }

    /* ---------------------------------------------------------------
       7. Importe en pesos y fecha minima
       --------------------------------------------------------------- */

    function iniciarImporte(campo) {
        var salida = acompanante(campo, '[data-money-text]');
        if (!salida) return;

        function pintar() {
            var valor = parseFloat(campo.value);
            if (isNaN(valor)) {
                salida.textContent = '';
                return;
            }
            salida.textContent = '$' + valor.toLocaleString('es-CO');
        }

        campo.addEventListener('input', pintar);
        pintar();
    }

    function iniciarFechaMinima(campo) {
        // El limite inferior es hoy: un trabajo no puede vencer en el pasado.
        if (campo.type !== 'date' || campo.getAttribute('min')) return;
        var hoy = new Date();
        var mes = String(hoy.getMonth() + 1).padStart(2, '0');
        var dia = String(hoy.getDate()).padStart(2, '0');
        campo.setAttribute('min', hoy.getFullYear() + '-' + mes + '-' + dia);
    }

    /* ---------------------------------------------------------------
       Arranque
       --------------------------------------------------------------- */

    function iniciar() {
        todos(document, '[data-wizard]').forEach(iniciarAsistente);
        todos(document, '[data-password-meter]').forEach(iniciarMedidor);
        todos(document, '[data-password-match]').forEach(iniciarConfirmacion);
        todos(document, '[data-tags]').forEach(iniciarEtiquetas);
        todos(document, 'input[type="file"]').forEach(iniciarCarga);
        todos(document, '[data-counter]').forEach(iniciarContador);
        todos(document, '[data-money]').forEach(iniciarImporte);
        todos(document, 'input[type="date"]').forEach(iniciarFechaMinima);

        // Validación en vivo: el error aparece mientras se escribe, no
        // despues de enviar.
        todos(document, 'input, select, textarea').forEach(function (campo) {
            if (campo.type === 'hidden' || campo.type === 'file') return;
            campo.addEventListener('blur', function () {
                if (campo.value || campo.required) validarCampo(campo);
            });
            campo.addEventListener('input', function () {
                if (campo.getAttribute('aria-invalid') === 'true') {
                    limpiarError(campo);
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();
