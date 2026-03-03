from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from scheduling.models import Appointment, MedicalRecord

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

class MedicalRecordsAPITests(APITestCase):
    def setUp(self):
        # PATIENT dueño de la cita
        self.patient = User.objects.create_user(
            username="patient_records",
            email="patient_records@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        # DOCTOR asignado
        self.doctor_assigned = User.objects.create_user(
            username="doctor_assigned",
            email="doctor_assigned@email.com",
            password="Password123!",
        )
        self.doctor_assigned.role = User.Role.DOCTOR
        self.doctor_assigned.save(update_fields=["role"])

        # DOCTOR no asignado
        self.doctor_other = User.objects.create_user(
            username="doctor_other",
            email="doctor_other@email.com",
            password="Password123!",
        )
        self.doctor_other.role = User.Role.DOCTOR
        self.doctor_other.save(update_fields=["role"])

        # CLINIC
        self.clinic = User.objects.create_user(
            username="clinic_records",
            email="clinic_records@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        # Cita asignada al doctor_assigned
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_assigned,
            scheduled_at=timezone.now() + timedelta(days=1),
            reason="Control general",
            status=Appointment.Status.CONFIRMED,
        )

        self.records_url = f"/api/appointments/{self.appointment.id}/records/"

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_assigned_doctor_can_create_record(self):
        self.auth_as(self.doctor_assigned)

        payload = {
            "diagnosis": "Hipertension controlada",
            "notes": "Paciente estable",
            "treatment": "Losartan 50mg cada 24h",
        }

        res = self.client.post(self.records_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)
        self.assertEqual(res.data["diagnosis"], payload["diagnosis"])

    def test_non_assigned_doctor_cannot_create_record(self):
        self.auth_as(self.doctor_other)

        payload = {
            "diagnosis": "No permitido",
            "notes": "No es doctor asignado",
            "treatment": "N/A",
        }

        res = self.client.post(self.records_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", res.data)

    def test_owner_patient_can_list_records(self):
        MedicalRecord.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_assigned,
            diagnosis="Diagnostico inicial",
            notes="Notas iniciales",
            treatment="Tratamiento inicial",
        )

        self.auth_as(self.patient)
        res = self.client.get(self.records_url, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["diagnosis"], "Diagnostico inicial")

    def test_clinic_can_list_records(self):
        MedicalRecord.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_assigned,
            diagnosis="Diagnostico para clinic",
            notes="Notas para clinic",
            treatment="Tratamiento para clinic",
        )

        self.auth_as(self.clinic)
        res = self.client.get(self.records_url, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
