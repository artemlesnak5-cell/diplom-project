"""Настройка админки: редактирование каталога и статусов заказов."""
from django.contrib import admin
from .models import Category, Order, OrderItem, Product

admin.site.site_header = 'Частная коллекция — управление магазином'
admin.site.site_title = 'Tissot · администратор'
admin.site.index_title = 'Товары и заказы'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'reference', 'category', 'price', 'stock', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'reference', 'color']
    prepopulated_fields = {'slug': ('name', 'color')}
    list_editable = ['price', 'stock', 'is_active']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ['product', 'name', 'reference', 'price', 'quantity']
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'phone', 'email', 'user__username']
    readonly_fields = ['number', 'checkout_token', 'user', 'full_name', 'phone', 'email', 'address', 'comment', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
