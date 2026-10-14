"""Фильтр rub форматирует цену в рублях для HTML-шаблонов."""
from django import template
register = template.Library()

@register.filter
def rub(value):
    text = f'{value:,.2f}'.replace(',', ' ').replace('.', ',')
    return (text[:-3] if text.endswith(',00') else text) + ' ₽'
