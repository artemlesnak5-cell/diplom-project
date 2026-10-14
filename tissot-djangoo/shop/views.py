"""Обработчики запросов: каталог, аккаунты, корзина и заказы пользователя."""
import uuid
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .cart import cart_items
from .forms import CheckoutForm, QuantityForm, RegistrationForm
from .models import Category, Order, Product
from .services import place_order

def home(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'shop/home.html', {'products': products[:3], 'hero': products.filter(slug='prx-blue').first() or products.first()})

def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    query = request.GET.get('q', '').strip()[:100]
    category = request.GET.get('collection', '')
    sort = request.GET.get('sort', '')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(reference__icontains=query) | Q(color__icontains=query))
    if category:
        products = products.filter(category__slug=category)
    products = products.order_by({'price': 'price', '-price': '-price', 'name': 'name'}.get(sort, 'id'), 'pk')
    return render(request, 'shop/catalog.html', {'products': products, 'categories': Category.objects.all(), 'q': query, 'selected_category': category, 'sort': sort})

def product(request, slug):
    item = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    return render(request, 'shop/product.html', {'product': item, 'quantity_form': QuantityForm(),
        'related': Product.objects.filter(category=item.category, is_active=True).exclude(pk=item.pk)[:3]})

def register(request):
    if request.user.is_authenticated:
        return redirect('orders')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Аккаунт создан. Теперь можно оформить заказ.')
        return redirect('cart')
    return render(request, 'registration/register.html', {'form': form})

def cart(request):
    rows, total = cart_items(request)
    return render(request, 'shop/cart.html', {'rows': rows, 'total': total})

@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    form = QuantityForm(request.POST)
    if form.is_valid():
        cart = request.session.get('cart', {}).copy()
        quantity = cart.get(str(pk), 0) + form.cleaned_data['quantity']
        if quantity <= min(product.stock, 10):
            cart[str(pk)] = quantity
            request.session['cart'] = cart
            messages.success(request, 'Товар добавлен в корзину.')
        else:
            messages.error(request, 'Недостаточно товара или превышен лимит 10 штук.')
    else:
        messages.error(request, 'Количество должно быть целым числом от 1 до 10.')
    return redirect('cart')

@require_POST
def cart_update(request, pk):
    cart = request.session.get('cart', {}).copy()
    product = get_object_or_404(Product, pk=pk, is_active=True)
    form = QuantityForm(request.POST)
    if str(pk) not in cart:
        messages.error(request, 'Товара нет в корзине.')
    elif form.is_valid() and form.cleaned_data['quantity'] <= product.stock:
        cart[str(pk)] = form.cleaned_data['quantity']
        request.session['cart'] = cart
    else:
        messages.error(request, 'Проверьте количество и доступный остаток.')
    return redirect('cart')

@require_POST
def cart_remove(request, pk):
    cart = request.session.get('cart', {}).copy()
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('cart')

@login_required
def checkout(request):
    rows, total = cart_items(request)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            # Повторная отправка формы должна открыть прежний заказ, а не создать новый.
            existing = Order.objects.filter(user=request.user, checkout_token=token).first()
            if existing:
                return redirect(existing)
            if str(token) != request.session.get('checkout_token'):
                form.add_error(None, 'Форма устарела. Откройте оформление заново.')
            else:
                details = {k: form.cleaned_data[k] for k in CheckoutForm.Meta.fields}
                try:
                    order = place_order(request.user, request.session.get('cart', {}), details, token)
                except ValueError as error:
                    form.add_error(None, str(error))
                except IntegrityError:
                    existing = Order.objects.filter(user=request.user, checkout_token=token).first()
                    if existing:
                        return redirect(existing)
                    raise
                else:
                    request.session['cart'] = {}
                    request.session.pop('checkout_token', None)
                    messages.success(request, 'Учебный заказ создан. Оплата не списывалась.')
                    return redirect(order)
    else:
        if not rows:
            messages.info(request, 'Сначала добавьте часы в корзину.')
            return redirect('cart')
        token = request.session.setdefault('checkout_token', str(uuid.uuid4()))
        form = CheckoutForm(initial={'token': token, 'email': request.user.email, 'full_name': request.user.get_full_name()})
    return render(request, 'shop/checkout.html', {'form': form, 'rows': rows, 'total': total})

@login_required
def orders(request):
    return render(request, 'shop/orders.html', {'orders': Order.objects.filter(user=request.user)})

@login_required
def order_detail(request, number):
    # Проверка владельца не позволяет открыть чужой заказ по известной ссылке.
    order = get_object_or_404(Order.objects.prefetch_related('items'), number=number, user=request.user)
    return render(request, 'shop/order_detail.html', {'order': order, 'statuses': Order.Status.choices})

def contacts(request):
    return render(request, 'shop/contacts.html')
