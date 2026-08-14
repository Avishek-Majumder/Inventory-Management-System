from django.contrib import admin

from inventory.models import Category, Customer, Invoice, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number']
    search_fields = ['name', 'email']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'quantity_in_stock']
    list_filter = ['category']
    search_fields = ['name', 'sku']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'quantity', 'price', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['customer__name', 'product__name']
