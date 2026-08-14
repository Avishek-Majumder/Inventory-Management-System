# Inventory Management System API

A Django REST Framework API for inventory sales, built with a custom user model,
JWT authentication, profile management, stock-aware invoices, and role-based
permissions.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows PowerShell
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run the automated tests with:

```bash
python manage.py test
```

## Authentication

Register with `POST /api/auth/register/`, then obtain tokens using
`POST /api/auth/login/` and send the access token on subsequent requests:

```http
Authorization: Bearer <access-token>
```

| Endpoint | Purpose |
| --- | --- |
| `POST /api/auth/register/` | Create a user and associated profile |
| `POST /api/auth/login/` | Obtain JWT access and refresh tokens |
| `POST /api/auth/login/refresh/` | Refresh an access token |
| `GET/PATCH /api/auth/me/` | Read or update the current user and profile |

Example registration body:

```json
{
  "username": "operator",
  "email": "operator@example.com",
  "password": "ComplexPass123!",
  "password2": "ComplexPass123!"
}
```

## Inventory endpoints and permissions

All inventory endpoints require authentication. Staff users can manage product
catalogue data; all authenticated users can manage customers.

| Resource | Endpoint | Who may modify it |
| --- | --- | --- |
| Categories | `/api/categories/` | Staff only |
| Customers | `/api/customers/` | Any authenticated user |
| Products | `/api/products/` | Staff only |
| Invoices | `/api/invoices/` | Create: authenticated user; edit/delete: creator or staff |
| Invoice report | `/api/invoices/report/` | Staff sees all totals; other users see their own totals |

The standard CRUD methods are supplied by DRF router endpoints, for example
`GET/POST /api/products/` and `GET/PATCH/DELETE /api/products/<id>/`.

## Invoice behavior

Create an invoice with a customer, product, quantity, and unit price:

```json
POST /api/invoices/
{
  "customer": 1,
  "product": 1,
  "quantity": 2,
  "price": "999.99"
}
```

Invoice creation locks the product, rejects insufficient stock, and deducts the
quantity. Editing an invoice safely reconciles its original and new quantities;
deleting it restores stock. The invoice price is preserved as the sale-time unit
price. `GET /api/invoices/report/` returns `total_invoices`, `total_sales`, and
`total_products_sold` for the requesting user's permitted invoice set.

## Validation

- Registration requires a unique email and matching, Django-valid password.
- Profile and customer phone numbers accept 7–20 digits with optional leading
  `+`, spaces, or hyphens.
- Category names and product SKUs cannot be blank; SKUs are trimmed and stored
  uppercase.
- Product and invoice prices must be greater than zero, and invoice quantity
  must be at least one.
