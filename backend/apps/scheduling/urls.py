from django.urls import path
from .views import assign_doctor
from .views import doctor_update_appointment
from .views import doctor_appointments, doctor_update_appointment_status
from .views import (
    appointments,
    appointment_detail,
    services,
    service_detail,
    appointment_services,
    appointment_service_detail,
    appointment_medical_records
)

urlpatterns = [
    path("appointments/", appointments),
    path("appointments/<int:pk>/", appointment_detail),

    path("services/", services),
    path("services/<int:pk>/", service_detail),

    path("appointments/<int:pk>/services/", appointment_services),
    path("appointments/<int:pk>/services/<int:item_id>/", appointment_service_detail),

    path("appointments/<int:pk>/assign-doctor/", assign_doctor),

    path("doctor/appointments/", doctor_appointments),
    path("doctor/appointments/<int:pk>/status/", doctor_update_appointment_status),

    path("doctor/appointments/<int:pk>/", doctor_update_appointment),

    path("appointments/<int:pk>/records/", appointment_medical_records),
]
