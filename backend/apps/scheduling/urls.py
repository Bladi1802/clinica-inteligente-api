from django.urls import path

from .views import (
    appointments,
    appointment_detail,
    services,
    service_detail,
    appointment_services,
    appointment_service_detail,
)

urlpatterns = [
    path("appointments/", appointments),
    path("appointments/<int:pk>/", appointment_detail),

    path("services/", services),
    path("services/<int:pk>/", service_detail),

    path("appointments/<int:pk>/services/", appointment_services),
    path("appointments/<int:pk>/services/<int:item_id>/", appointment_service_detail),
]
