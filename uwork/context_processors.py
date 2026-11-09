"""Context processors del proyecto."""


def csp_nonce(request):
    """Expone el nonce de la CSP a todas las plantillas.

    Uso en la plantilla: `<script nonce="{{ csp_nonce }}">`. Si el middleware
    no está activo el valor es vacío y el navegador bloquea el script: es
    preferible a servirlo sin nonce.
    """
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}
