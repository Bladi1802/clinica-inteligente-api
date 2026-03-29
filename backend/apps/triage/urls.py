from django.urls import path

from .views import appointment_triage

urlpatterns = [
    path("appointments/<int:pk>/triage/", appointment_triage),
]
