from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import locale

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter(name='accessible')
def accessible(field, css_class=''):
    """Renderiza un campo combining clase CSS y error accesible.

    WCAG 3.3.1 y 4.1.3 (§6.6): añade aria-describedby y aria-invalid al
    widget cuando el campo tiene error, para que el lector de pantalla
    asocie el mensaje al control. El texto visible no se oculta: el error
    se sigue leyendo y además se anuncia.

    Este filtro reemplaza la cadena |accessible|add_class: encadenarlos no
    funciona porque el primero ya devuelve el widget renderizado.
    """
    attrs = {}
    if css_class:
        attrs['class'] = css_class
    if field.errors:
        attrs['aria-invalid'] = 'true'
        attrs['aria-describedby'] = '{}-error'.format(field.id_for_label)
    elif field.help_text:
        attrs['aria-describedby'] = '{}-help'.format(field.id_for_label)
    return field.as_widget(attrs=attrs)


@register.simple_tag
def field_error(field):
    """Mensaje de error de un campo, anunciable con role=alert.

    Usa la clase .field__error del sistema de diseño, de modo que el
    error se ve igual en todos los formularios: glifo, texto y color de
    estado, con el icono marcado como decorativo para el lector de
    pantalla.
    """
    if not field.errors:
        return ''
    return mark_safe(
        '<div class="field__error" role="alert" id="{}-error">'
        '<i class="bi bi-exclamation-circle" aria-hidden="true"></i> <span>{}</span></div>'
        .format(field.id_for_label, conditional_escape(field.errors[0]))
    )


@register.filter(name='split')
def split(value, delimiter=','):
    return [item.strip() for item in value.split(delimiter) if item.strip()]


@register.filter(name='cop')
def cop(value):
    """Format a number as Colombian Pesos: $350.000"""
    try:
        value = int(float(value))
        formatted = f'{value:,.0f}'.replace(',', '.')
        return f'${formatted}'
    except (ValueError, TypeError):
        return value


@register.filter(name='nota')
def nota(value):
    """Format a rating with a decimal comma: 4,5"""
    try:
        valor = float(value)
    except (ValueError, TypeError):
        return value
    return f'{valor:.1f}'.replace('.', ',')


@register.filter(name='cop_corto')
def cop_corto(value):
    """Importe abreviado para etiquetas estrechas: $1,2M, $380K.

    El formato completo ($380.000) no cabe bajo una columna de un grafico
    con doce meses.
    """
    try:
        valor = float(value)
    except (ValueError, TypeError):
        return value
    if valor >= 1000000:
        return '$' + f'{valor / 1000000:,.1f}'.replace('.', ',') + 'M'
    if valor >= 1000:
        return '$' + f'{valor / 1000:,.0f}' + 'K'
    return '$' + f'{valor:,.0f}'
