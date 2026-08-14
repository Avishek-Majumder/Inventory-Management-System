from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """Authenticated users may read; staff users may modify."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsInvoiceOwnerOrStaff(permissions.BasePermission):
    """Authenticated users create invoices; owners and staff modify them."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.created_by_id == request.user.id
