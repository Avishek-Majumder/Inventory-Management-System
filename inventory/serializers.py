import re

from rest_framework import serializers

from inventory.models import Category, Customer, Invoice, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Category name cannot be blank.')
        return value

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number', 'address', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_phone_number(self, value):
        if value and not re.fullmatch(r'\+?[0-9\-\s]{7,20}', value):
            raise serializers.ValidationError('Enter a valid phone number.')
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name', 'sku', 'description',
            'price', 'quantity_in_stock', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_sku(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError('SKU cannot be blank.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value
    def validate_quantity_in_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('Quantity in stock cannot be negative.')
        return value


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'customer', 'customer_name', 'product', 'product_name',
            'quantity', 'price', 'total_price', 'created_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be at least 1.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value
