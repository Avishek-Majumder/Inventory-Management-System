from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from inventory.models import Category, Customer, Invoice, Product


class InventoryApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', 'staff@example.com', 'ComplexPass123!', is_staff=True)
        self.owner = User.objects.create_user('owner', 'owner@example.com', 'ComplexPass123!')
        self.other = User.objects.create_user('other', 'other@example.com', 'ComplexPass123!')
        self.category = Category.objects.create(name='Electronics')
        self.customer = Customer.objects.create(name='Acme Ltd')
        self.product = Product.objects.create(
            name='Keyboard', category=self.category, sku='KEY-001', price=Decimal('50.00'), quantity_in_stock=10,
            created_by=self.staff,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def invoice_payload(self, **overrides):
        payload = {'customer': self.customer.pk, 'product': self.product.pk, 'quantity': 3, 'price': '50.00'}
        payload.update(overrides)
        return payload

    def test_anonymous_requests_are_rejected(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_only_staff_can_modify_products(self):
        self.authenticate(self.owner)
        denied = self.client.post('/api/products/', {
            'name': 'Mouse', 'category': self.category.pk, 'sku': 'MOUSE-001',
            'price': '25.00', 'quantity_in_stock': 5,
        }, format='json')
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.staff)
        accepted = self.client.post('/api/products/', {
            'name': 'Mouse', 'category': self.category.pk, 'sku': ' mouse-001 ',
            'price': '25.00', 'quantity_in_stock': 5,
        }, format='json')
        self.assertEqual(accepted.status_code, status.HTTP_201_CREATED)
        self.assertEqual(accepted.data['sku'], 'MOUSE-001')

    def test_validation_rejects_invalid_values(self):
        self.authenticate(self.staff)
        product = self.client.post('/api/products/', {
            'name': 'Broken', 'category': self.category.pk, 'sku': '   ',
            'price': '0', 'quantity_in_stock': 0,
        }, format='json')
        self.assertEqual(product.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('sku', product.data)
        self.assertIn('price', product.data)

        self.authenticate(self.owner)
        invoice = self.client.post('/api/invoices/', self.invoice_payload(quantity=0), format='json')
        self.assertEqual(invoice.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', invoice.data)

    def test_invoice_create_update_delete_reconciles_stock(self):
        self.authenticate(self.owner)
        created = self.client.post('/api/invoices/', self.invoice_payload(), format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 7)

        updated = self.client.patch(f"/api/invoices/{created.data['id']}/", {'quantity': 5}, format='json')
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 5)

        deleted = self.client.delete(f"/api/invoices/{created.data['id']}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 10)

    def test_overselling_is_rejected_without_stock_change(self):
        self.authenticate(self.owner)
        response = self.client.post('/api/invoices/', self.invoice_payload(quantity=11), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_in_stock, 10)

    def test_invoice_owner_and_visibility_rules(self):
        invoice = Invoice.objects.create(
            customer=self.customer, product=self.product, quantity=1, price=Decimal('50.00'), created_by=self.owner,
        )
        self.authenticate(self.other)
        self.assertEqual(self.client.get('/api/invoices/').data['count'], 0)
        self.assertEqual(self.client.patch(f'/api/invoices/{invoice.pk}/', {'price': '45.00'}, format='json').status_code,
                         status.HTTP_404_NOT_FOUND)

        self.authenticate(self.staff)
        self.assertEqual(self.client.patch(f'/api/invoices/{invoice.pk}/', {'price': '45.00'}, format='json').status_code,
                         status.HTTP_200_OK)

    def test_report_is_scoped_to_caller(self):
        Invoice.objects.create(customer=self.customer, product=self.product, quantity=2, price=Decimal('10.00'), created_by=self.owner)
        Invoice.objects.create(customer=self.customer, product=self.product, quantity=4, price=Decimal('5.00'), created_by=self.other)

        self.authenticate(self.owner)
        own_report = self.client.get('/api/invoices/report/')
        self.assertEqual(own_report.data['total_invoices'], 1)
        self.assertEqual(Decimal(str(own_report.data['total_sales'])), Decimal('20'))
        self.assertEqual(own_report.data['total_products_sold'], 2)

        self.authenticate(self.staff)
        staff_report = self.client.get('/api/invoices/report/')
        self.assertEqual(staff_report.data['total_invoices'], 2)
        self.assertEqual(Decimal(str(staff_report.data['total_sales'])), Decimal('40'))
