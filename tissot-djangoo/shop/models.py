"""Структура базы: коллекции, товары, заказы и позиции заказов."""
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField('Коллекция', max_length=80)
    slug = models.SlugField('Адрес', unique=True)

    class Meta:
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Коллекция')
    name = models.CharField('Название', max_length=150)
    slug = models.SlugField('Адрес страницы', unique=True)
    reference = models.CharField('Артикул', max_length=40, unique=True)
    color = models.CharField('Циферблат', max_length=100)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена, ₽', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField('Остаток', default=0)
    diameter = models.PositiveSmallIntegerField('Диаметр, мм', default=40)
    image = models.ImageField('Фото', upload_to='watches/', blank=True)
    is_active = models.BooleanField('Опубликован', default=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['id']
        constraints = [models.CheckConstraint(condition=models.Q(price__gt=0), name='product_price_positive')]

    def __str__(self):
        return f'{self.name} / {self.reference}'

    def get_absolute_url(self):
        return reverse('product', args=[self.slug])


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        CONFIRMED = 'confirmed', 'Подтверждён'
        SHIPPED = 'shipped', 'Отправлен'
        COMPLETED = 'completed', 'Завершён'

    number = models.UUIDField('Номер', default=uuid.uuid4, unique=True, editable=False)
    checkout_token = models.UUIDField(unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name='Покупатель')
    full_name = models.CharField('Получатель', max_length=150)
    phone = models.CharField('Телефон', max_length=30)
    email = models.EmailField('Email')
    address = models.CharField('Адрес доставки', max_length=300)
    comment = models.TextField('Комментарий', blank=True, max_length=1000)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField('Сумма, ₽', max_digits=12, decimal_places=2)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.pk} — {self.full_name}'

    def get_absolute_url(self):
        return reverse('order_detail', args=[self.number])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    # Снимок данных товара: изменения каталога не должны менять оформленный заказ.
    name = models.CharField('Название при покупке', max_length=150)
    reference = models.CharField('Артикул при покупке', max_length=40)
    price = models.DecimalField('Цена при покупке', max_digits=10, decimal_places=2)
    quantity = models.PositiveSmallIntegerField('Количество', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gte=1), name='order_item_quantity_positive')]

    @property
    def subtotal(self):
        return self.price * self.quantity
