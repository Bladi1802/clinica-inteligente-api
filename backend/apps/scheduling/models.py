from django.db import models
from django.conf import settings

# Create your models here.

class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
    )

    scheduled_at = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment({self.patient_id}) @ {self.scheduled_at}"

class Service(models.Model):
    name = models.CharField(max_length=120, unique=True)
    duration_minutes = models.PositiveIntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AppointmentService(models.Model):
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.CASCADE,
        related_name="appointment_services",
    )
    service = models.ForeignKey(
        "scheduling.Service",
        on_delete=models.PROTECT,
        related_name="service_appointments",
    )

    quantity = models.PositiveIntegerField(default=1)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["appointment", "service"], name="uniq_appointment_service")
        ]

    def __str__(self):
        return f"{self.appointment_id} - {self.service_id}"
