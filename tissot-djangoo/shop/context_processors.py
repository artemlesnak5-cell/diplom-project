"""Передаёт количество товаров в корзине во все HTML-шаблоны."""
def cart_count(request):
    return {'cart_count': sum(q for q in request.session.get('cart', {}).values() if isinstance(q, int) and 1 <= q <= 10)}
