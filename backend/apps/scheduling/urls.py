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
    appointment_medical_records,
    appointment_medical_record_detail,
    clinic_appointments,
    dashboard_summary,
    dashboard_trends,
    doctor_schedules,
    doctor_schedule_detail,
    appointment_reschedule,
    appointment_reminders,
    send_appointment_reminder,
    appointment_telemedicine,
    telemedicine_prescription,
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

    path("appointments/<int:pk>/records/<int:record_id>/", appointment_medical_record_detail),
    path("clinic/appointments/", clinic_appointments),

    path("dashboard/summary/", dashboard_summary),
    path("dashboard/trends/", dashboard_trends), 

    path("clinic/doctor-schedules/", doctor_schedules),
    path("clinic/doctor-schedules/<int:schedule_id>/", doctor_schedule_detail),

    path("appointments/<int:pk>/reschedule/", appointment_reschedule),

    path("appointments/<int:pk>/reminders/", appointment_reminders),
    path("appointments/<int:pk>/reminders/<int:reminder_id>/send/", send_appointment_reminder),

    path("appointments/<int:pk>/telemedicine/", appointment_telemedicine),

    path("telemedicine/<int:pk>/prescription/", telemedicine_prescription),

]
