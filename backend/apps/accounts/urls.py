from django.urls import path
from .views import me, register

urlpatterns = [
    path("auth/me/", me),
    path("auth/register/", register),
]

