from django.urls import path

from .views import create_patient_user, create_staff_user, me, register

urlpatterns = [
    path("auth/me/", me),
    path("auth/register/", register),
    path("auth/patients/", create_patient_user),
    path("auth/staff-users/", create_staff_user),
]
