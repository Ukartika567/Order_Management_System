from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSellerOrAdmin(BasePermission):
    """Custom permission to allow only sellers and admin users to modify products.Customers & unauthenticated users can only view."""

    def has_permission(self, request, view):
        # Allow GET, HEAD, or OPTIONS requests for everyone (read-only)
        if request.method in SAFE_METHODS:
            return True

        # Allow Create, Update, Delete only for sellers or admin users
        return request.user.is_authenticated and (request.user.is_seller or request.user.is_staff)
