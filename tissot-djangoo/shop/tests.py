import uuid
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from .models import Category, Order, Product
from .services import place_order

class StoreTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='PRX', slug='prx')
        self.product = Product.objects.create(category=category, name='Tissot PRX', slug='prx-blue',
            reference='T137.410.11.041.00', color='Синий', price='20000.00', stock=5)
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'Valid-test-pass-928!')
        self.details = {'full_name': 'Учебный покупатель', 'phone': '+7 999 000-00-00',
            'email': 'buyer@example.com', 'address': 'Учебный город, дом 1', 'comment': ''}

    def test_public_pages_and_search(self):
        for name in ['home', 'catalog', 'contacts', 'cart', 'register', 'login']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get(self.product.get_absolute_url()), self.product.reference)
        self.assertContains(self.client.get(reverse('catalog'), {'q': 'несуществующий'}), 'Ничего не найдено')
        self.assertContains(self.client.get(reverse('catalog'), {'collection': 'prx', 'q': 'Синий'}), self.product.reference)

    def test_registration_and_login(self):
        response = self.client.post(reverse('register'), {'username': 'newbuyer', 'email': 'new@example.com',
            'password1': 'Long-unique-password-731!', 'password2': 'Long-unique-password-731!'})
        self.assertRedirects(response, reverse('cart'))
        user = User.objects.get(username='newbuyer')
        self.assertTrue(user.check_password('Long-unique-password-731!'))
        self.assertNotEqual(user.password, 'Long-unique-password-731!')
        self.assertEqual(self.client.post(reverse('logout')).status_code, 302)
        self.assertEqual(self.client.get(reverse('orders')).status_code, 302)

    def test_cart_requires_post_and_csrf(self):
        url = reverse('cart_add', args=[self.product.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        protected = Client(enforce_csrf_checks=True)
        self.assertEqual(protected.post(url, {'quantity': 1}).status_code, 403)

    def test_cart_validation_update_and_remove(self):
        add = reverse('cart_add', args=[self.product.pk])
        for quantity in ['-1', '0', '99', 'abc']:
            self.client.post(add, {'quantity': quantity})
            self.assertFalse(self.client.session.get('cart'))
        self.client.post(add, {'quantity': 2, 'price': '1'})
        self.assertContains(self.client.get(reverse('cart')), '40 000 ₽')
        self.client.post(reverse('cart_update', args=[self.product.pk]), {'quantity': 3})
        self.assertEqual(self.client.session['cart'][str(self.product.pk)], 3)
        self.client.post(reverse('cart_remove', args=[self.product.pk]))
        self.assertEqual(self.client.session['cart'], {})

    def test_checkout_requires_login(self):
        self.assertEqual(self.client.get(reverse('checkout')).status_code, 302)

    def test_full_checkout_and_duplicate_submit(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add', args=[self.product.pk]), {'quantity': 2})
        self.assertEqual(self.client.get(reverse('checkout')).status_code, 200)
        token = self.client.session['checkout_token']
        data = {**self.details, 'token': token, 'total': '1'}
        response = self.client.post(reverse('checkout'), data)
        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.total, Decimal('40000.00'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(self.client.session['cart'], {})
        self.client.post(reverse('checkout'), data)
        self.assertEqual(Order.objects.count(), 1)

    def test_insufficient_stock_rolls_back(self):
        with self.assertRaises(ValueError):
            place_order(self.user, {str(self.product.pk): 6}, self.details, uuid.uuid4())
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_price_snapshot_and_order_access(self):
        order = place_order(self.user, {str(self.product.pk): 1}, self.details, uuid.uuid4())
        self.product.price = '25000.00'
        self.product.save()
        self.assertEqual(order.items.get().price, Decimal('20000.00'))
        other = User.objects.create_user('other', password='Another-test-pass-621!')
        self.client.force_login(other)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
        self.client.force_login(self.user)
        order.status = Order.Status.SHIPPED
        order.save()
        self.assertContains(self.client.get(order.get_absolute_url()), 'Отправлен')

    def test_invalid_checkout_token(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add', args=[self.product.pk]), {'quantity': 1})
        response = self.client.post(reverse('checkout'), {**self.details, 'token': str(uuid.uuid4())})
        self.assertContains(response, 'Форма устарела')
        self.assertEqual(Order.objects.count(), 0)

    def test_inactive_product_and_empty_checkout(self):
        self.product.is_active = False
        self.product.save()
        self.assertEqual(self.client.get(self.product.get_absolute_url()).status_code, 404)
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('cart'))

    def test_non_staff_cannot_change_status(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/admin/shop/order/').status_code, 302)

    def test_seed_does_not_reset_stock(self):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        Product.objects.filter(pk=self.product.pk).update(stock=2)
        call_command('seed_demo', verbosity=0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)
