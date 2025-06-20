from rest_framework.permissions import BasePermission


class IsAdminOrCreator(BasePermission):
    """
    - Any authenticated user can create (POST).
    - Only the object's creator or an admin can do rest of the things on the object.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_admin
