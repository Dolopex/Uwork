from django import template
import locale

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


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
