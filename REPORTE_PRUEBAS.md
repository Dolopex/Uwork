# R12 — Reporte de pruebas funcionales
# Indicador: Lista de chequeo firmada · Meta: >80 % pasados · Estado: En curso
#
# Este archivo es la lista de chequeo. Cada caso se ejecuta manualmente sobre
# la aplicacion en ejecucion; cuando termine la ronda, se marca Passed/Failed y
# se calcula el porcentaje al final.
#
# Uso:
#   1. Levantar la app:      python manage.py runserver
#   2. Datos de prueba:      python manage.py seed_data
#   3. Recorrer la lista y marcar cada caso.
#   4. Al final, contar Passed vs Failed y llenar el resumen.

## Datos de prueba

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| Empleador | techcorp | demo1234 |
| Empleador | creativestudio | demo1234 |
| Estudiante | ana_garcia | demo1234 |
| Estudiante | carlos_lopez | demo1234 |

## Bloque A — Autenticacion y registro

| # | Caso | Resultado |
| - | ---- | --------- |
| A1 | La pantalla inicial permite elegir entre estudiante y empleador | |
| A2 | El registro de estudiante acepta solo correo `@campusuninunez.edu.co` (R10) | |
| A3 | El registro de estudiante rechaza un correo personal | |
| A4 | El registro de empleador acepta un correo personal | |
| A5 | Tras registrarse, se muestra "revisa tu correo" y NO se inicia sesion (R11) | |
| A6 | El enlace del correo activa la cuenta | |
| A7 | El login se rechaza antes de verificar y explica por que (R11) | |
| A8 | "Reenviar verificacion" envia un enlace nuevo | |
| A9 | "Olvidar mi contrasena" envia el enlace de restablecimiento (R2) | |
| A10 | El enlace de restablecimiento permite crear una contrasena nueva | |
| A11 | "Cambiar contrasena" desde Perfil > Seguridad funciona | |
| A12 | Un enlace de restablecimiento ya usado no funciona dos veces | |
| A13 | Cerrar sesion funciona y vuelve a la pantalla inicial | |

## Bloque B — Perfil

| # | Caso | Resultado |
| - | ---- | --------- |
| B1 | La pestana Info muestra los datos registrados | |
| B2 | Editar perfil guarda los cambios | |
| B3 | La pestana Reseñas muestra las calificaciones recibidas | |
| B4 | La pestana Seguridad muestra el estado de verificacion del correo | |
| B5 | "Eliminar mi cuenta" exige la contrasena correcta (R16) | |
| B6 | Con contrasena incorrecta, la cuenta NO se elimina | |
| B7 | Con contrasena correcta, la cuenta se elimina y se cierra la sesion (R16) | |
| B8 | Tras eliminar la cuenta, sus trabajos y postulaciones ya no existen | |
| B9 | La foto de perfil se sube y se ve en el perfil publico | |
| B10 | Un archivo que no es imagen (por ejemplo .php) es rechazado (§6.5.3) | |
| B11 | Una imagen mayor a 5 MB es rechazada (§6.5.3) | |

## Bloque C — Trabajos y postulaciones

| # | Caso | Resultado |
| - | ---- | --------- |
| C1 | Un estudiante no puede publicar un trabajo | |
| C2 | Un empleador publica un trabajo correctamente | |
| C3 | El trabajo publicado aparece en la lista de explorar | |
| C4 | El detalle del trabajo muestra los datos completos | |
| C5 | Un estudiante se postula a un trabajo disponible | |
| C6 | No se puede postularse dos veces al mismo trabajo | |
| C7 | El empleador ve la lista de postulantes | |
| C8 | El empleador acepta un postulante y el trabajo pasa a "en proceso" | |
| C9 | Los demas postulados reciben la notificacion de rechazo | |
| C10 | El empleador marca el trabajo como finalizado | |
| C11 | Las calificaciones solo se pueden crear sobre trabajos finalizados | |

## Bloque D — Moderacion (§6.5.4)

| # | Caso | Resultado |
| - | ---- | --------- |
| D1 | El boton "Reportar publicacion" aparece en un trabajo ajeno | |
| D2 | El boton NO aparece en la propia publicacion | |
| D3 | Enviar un reporte crea una fila en el panel de moderacion | |
| D4 | Un usuario no puede abrir el panel de moderacion (solo staff) | |
| D5 | Un staff puede resolver un reporte y la publicacion desaparece | |
| D6 | El reporte sigue existiendo tras retirar el contenido (evidencia) | |
| D7 | "Sancionar" registra la fila en la bitacora con quien, cuando y por que | |
| D8 | El usuario sancionado pierde el acceso al siguiente request (force-logout) | |
| D9 | Un baneo temporal se levanta solo al vencer el plazo | |
| D10 | Un staff puede levantar un baneo manualmente desde la bitacora | |
| D11 | El usuario sancionado puede registrar una apelacion | |
| D12 | Aceptar una apelacion levanta el baneo y responde al usuario | |
| D13 | La bitacora no permite editar ni borrar filas desde el admin | |

## Bloque E — Seguridad y plataforma

| # | Caso | Resultado |
| - | ---- | --------- |
| E1 | La respuesta incluye `X-Content-Type-Options: nosniff` (§6.5.3) | |
| E2 | La respuesta incluye `X-Frame-Options: DENY` (§6.5.3) | |
| E3 | La respuesta incluye `Referrer-Policy` (§6.5.3) | |
| E4 | En produccion, la respuesta incluye HSTS (§6.5.3) | |
| E5 | Tras 5 intentos de registro seguidos se muestra el limite (§6.5.3) | |
| E6 | Tras 8 intentos de login seguidos se muestra el limite (§6.5.3) | |
| E7 | La tabla de permisos y los formularios validan contrasenas debiles | |
| E8 | Los terminos y condiciones son accesibles sin iniciar sesion (R14) | |
| E9 | La politica de privacidad es accesible sin iniciar sesion (R15) | |
| E10 | Los enlaces legales aparecen en el pie de pagina y en la pantalla inicial | |
| E11 | `python manage.py test` pasa completo sin errores | |
| E12 | `python manage.py check --deploy` no reporta errores | |

## Resumen

```
Casos ejecutados: ___
Pasados:          ___  (___ %)
Fallados:         ___
```

Meta declarada: **>80 % pasados**.

Casos fallados y accion correctiva:

| # | Que fallo | Causa | Correccion |
| - | --------- | ----- | ---------- |
|   |           |       |            |

---

Fecha de ejecucion: ____________
Ejecutado por: ____________
Firma: ____________
