from django.urls import path
from .views import AppointmentListCreateView, AppointmentCancelView

urlpatterns = [
    path("appointments/", AppointmentListCreateView.as_view()),
    path("appointments/<int:pk>/cancel/", AppointmentCancelView.as_view()),
]
