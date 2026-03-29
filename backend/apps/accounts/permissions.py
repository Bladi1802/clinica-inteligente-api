from rest_framework.permissions import BasePermission


class IsClinic(BasePermission):
    message = "Solo CLINIC puede realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "CLINIC"
        )
    
class IsDoctor(BasePermission):
    message = "Solo DOCTOR puede realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "DOCTOR"
        )

class IsClinicOrDoctor(BasePermission):
    message = "Solo CLINIC o DOCTOR puede realizar esta accion."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in {"CLINIC", "DOCTOR"}
        )
