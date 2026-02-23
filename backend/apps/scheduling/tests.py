from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class SchedulingAPITests(APITestCase):
    """
    Tests del Scheduling MVP:
    1) PATIENT no puede crear servicios (403)
    2) CLINIC sí puede crear servicios (201)
    3) PATIENT sí puede crear cita (201)
    4) No se puede crear cita en el pasado (400)
    """

    def setUp(self):
        # PATIENT
        self.patient = User.objects.create_user(
            username="patient_test",
            email="patient_test@email.com",
            password="Password123!",
        )
        if hasattr(self.patient, "role"):
            self.patient.role = User.Role.PATIENT
            self.patient.save(update_fields=["role"])

        # CLINIC (admin del negocio)
        self.clinic = User.objects.create_user(
            username="clinic_test",
            email="clinic_test@email.com",
            password="Password123!",
        )
        if hasattr(self.clinic, "role"):
            self.clinic.role = User.Role.CLINIC
            self.clinic.save(update_fields=["role"])

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    # -----------------------------
    # SERVICES
    # -----------------------------

    def test_patient_cannot_create_service(self):
        self.auth_as(self.patient)

        payload = {
            "name": "Servicio X",
            "base_price": "100.00",
            "duration_minutes": 30,
            "is_active": True
        }

        res = self.client.post("/api/services/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", res.data)

    def test_clinic_can_create_service(self):
        self.auth_as(self.clinic)

        payload = {
            "name": "Consulta general",
            "base_price": "350.00",
            "duration_minutes": 30,
            "is_active": True
        }

        res = self.client.post("/api/services/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)

    # -----------------------------
    # APPOINTMENTS
    # -----------------------------

    def test_patient_can_create_appointment(self):
        self.auth_as(self.patient)

        future_dt = timezone.now() + timedelta(days=2)

        payload = {
            "scheduled_at": future_dt.isoformat(),
            "reason": "Consulta general"
        }

        res = self.client.post("/api/appointments/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)

    def test_patient_cannot_create_appointment_in_past(self):
        self.auth_as(self.patient)

        past_dt = timezone.now() - timedelta(days=1)

        payload = {
            "scheduled_at": past_dt.isoformat(),
            "reason": "No debe permitir"
        }

        res = self.client.post("/api/appointments/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("scheduled_at", res.data)