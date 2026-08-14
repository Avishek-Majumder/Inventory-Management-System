from rest_framework.routers import DefaultRouter

from inventory.views import CategoryViewSet, CustomerViewSet, InvoiceViewSet, ProductViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('customers', CustomerViewSet, basename='customer')
router.register('products', ProductViewSet, basename='product')
router.register('invoices', InvoiceViewSet, basename='invoice')

urlpatterns = router.urls
