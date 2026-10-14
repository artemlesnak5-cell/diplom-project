"""Чтение корзины из сессии и расчёт стоимости по актуальным ценам товаров."""
from decimal import Decimal
from .models import Product

def cart_items(request):
    """В сессии — только ID и количество. Цены всегда берём из БД."""
    cart = request.session.get('cart', {})
    products = Product.objects.filter(pk__in=[int(k) for k in cart if str(k).isdigit()], is_active=True)
    rows = []
    for product in products:
        quantity = cart.get(str(product.pk), 0)
        if isinstance(quantity, int) and 1 <= quantity <= 10:
            rows.append({'product': product, 'quantity': quantity, 'subtotal': product.price * quantity})
    return rows, sum((row['subtotal'] for row in rows), Decimal('0.00'))
