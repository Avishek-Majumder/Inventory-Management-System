from django.db import transaction
from django.db.models import F, Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from inventory.models import Category, Customer, Invoice, Product
from inventory.permissions import IsInvoiceOwnerOrStaff, IsStaffOrReadOnly
from inventory.serializers import CategorySerializer, CustomerSerializer, InvoiceSerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'created_by').all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsInvoiceOwnerOrStaff]

    def get_queryset(self):
        queryset = Invoice.objects.select_related('customer', 'product', 'created_by')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(created_by=self.request.user)

    @staticmethod
    def _deduct_stock(product, quantity):
        if quantity > product.quantity_in_stock:
            raise ValidationError({
                'quantity': f'Only {product.quantity_in_stock} unit(s) of "{product.name}" left in stock.'
            })
        product.quantity_in_stock -= quantity
        product.save(update_fields=['quantity_in_stock', 'updated_at'])

    def perform_create(self, serializer):
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=serializer.validated_data['product'].pk)
            self._deduct_stock(product, serializer.validated_data['quantity'])
            serializer.save(created_by=self.request.user, product=product)

    def perform_update(self, serializer):
        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(pk=serializer.instance.pk)
            requested_product_id = serializer.validated_data.get('product', invoice.product).pk
            product_ids = sorted({invoice.product_id, requested_product_id})
            locked_products = {
                product.pk: product
                for product in Product.objects.select_for_update().filter(pk__in=product_ids).order_by('pk')
            }
            old_product = locked_products[invoice.product_id]
            new_product = locked_products[requested_product_id]
            old_product.quantity_in_stock += invoice.quantity
            old_product.save(update_fields=['quantity_in_stock', 'updated_at'])

            new_quantity = serializer.validated_data.get('quantity', invoice.quantity)
            self._deduct_stock(new_product, new_quantity)
            serializer.instance = invoice
            serializer.save(product=new_product)

    def perform_destroy(self, instance):
        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(pk=instance.pk)
            product = Product.objects.select_for_update().get(pk=invoice.product_id)
            product.quantity_in_stock += invoice.quantity
            product.save(update_fields=['quantity_in_stock', 'updated_at'])
            invoice.delete()

    @action(detail=False, methods=['get'], url_path='report')
    def report(self, request):
        queryset = self.get_queryset()
        aggregates = queryset.aggregate(
            total_sales=Sum(F('quantity') * F('price')),
            total_products_sold=Sum('quantity'),
        )
        return Response({
            'total_invoices': queryset.count(),
            'total_sales': aggregates['total_sales'] or 0,
            'total_products_sold': aggregates['total_products_sold'] or 0,
        })
