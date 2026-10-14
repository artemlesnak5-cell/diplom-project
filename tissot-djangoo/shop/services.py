"""Создание заказа: проверка остатка, фиксация цены и списание товаров."""
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from .models import Order, OrderItem, Product

@transaction.atomic
def place_order(user, cart, details, token):
    """Заказ и списание остатка проходят одной транзакцией: всё или ничего."""
    existing = Order.objects.filter(user=user, checkout_token=token).first()
    if existing:
        return existing
    ids = [int(k) for k in cart if str(k).isdigit()]
    products = list(Product.objects.select_for_update().filter(pk__in=ids).order_by('pk'))
    if not cart or len(products) != len(cart):
        raise ValueError('Корзина изменилась. Проверьте её перед оформлением.')
    total = Decimal('0.00')
    for product in products:
        quantity = cart.get(str(product.pk))
        if not isinstance(quantity, int) or not 1 <= quantity <= 10:
            raise ValueError('Некорректное количество товара.')
        if not product.is_active or product.stock < quantity:
            raise ValueError(f'{product.name} ({product.reference}): недостаточно товара в наличии.')
        total += product.price * quantity
    order = Order.objects.create(user=user, checkout_token=token, total=total, **details)
    for product in products:
        quantity = cart[str(product.pk)]
        changed = Product.objects.filter(pk=product.pk, stock__gte=quantity).update(stock=F('stock') - quantity)
        if changed != 1:
            raise ValueError('Остаток изменился. Обновите корзину.')
        OrderItem.objects.create(order=order, product=product, name=product.name,
                                 reference=product.reference, price=product.price, quantity=quantity)
    return order
