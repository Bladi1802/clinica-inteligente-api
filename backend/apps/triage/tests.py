from django.test import TestCase

# Create your tests here.

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from scheduling.models import Appointment
from triage.models import TriageAssessment


User = get_user_model()


class TriageAPITests(APITestCase):
    def setUp(self):
        # Usuarios
        self.patient_owner = User.objects.create_user(
            username="triage_patient_owner",
            email="triage_patient_owner@email.com",
            password="Password123!",
        )
        self.patient_owner.role = User.Role.PATIENT
        self.patient_owner.save(update_fields=["role"])

        self.patient_other = User.objects.create_user(
            username="triage_patient_other",
            email="triage_patient_other@email.com",
            password="Password123!",
        )
        self.patient_other.role = User.Role.PATIENT
        self.patient_other.save(update_fields=["role"])

        self.doctor_assigned = User.objects.create_user(
            username="triage_doctor_assigned",
            email="triage_doctor_assigned@email.com",
            password="Password123!",
        )
        self.doctor_assigned.role = User.Role.DOCTOR
        self.doctor_assigned.save(update_fields=["role"])

        self.doctor_other = User.objects.create_user(
            username="triage_doctor_other",
            email="triage_doctor_other@email.com",
            password="Password123!",
        )
        self.doctor_other.role = User.Role.DOCTOR
        self.doctor_other.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="triage_clinic",
            email="triage_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        # Cita
        self.appointment = Appointment.objects.create(
            patient=self.patient_owner,
            doctor=self.doctor_assigned,
            scheduled_at=timezone.now() + timedelta(days=1),
            reason="Consulta triage",
            status=Appointment.Status.CONFIRMED,
        )

        self.url = f"/api/appointments/{self.appointment.id}/triage/"

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_owner_patient_can_create_triage(self):
        self.auth_as(self.patient_owner)

        payload = {
            "chief_complaint": "Dolor toracico con falta de aire",
            "answers": {
                "fiebre": False,
                "dificultad_respiratoria": True,
                "dolor_escala": 8,
            },
        }

        res = self.client.post(self.url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)
        self.assertIn("risk_score", res.data)
        self.assertIn("risk_level", res.data)

    def test_cannot_create_second_triage_for_same_appointment(self):
        self.auth_as(self.patient_owner)

        first_payload = {
            "chief_complaint": "Molestia general",
            "answers": {"dolor_escala": 2},
        }
        first = self.client.post(self.url, first_payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second_payload = {
            "chief_complaint": "Nuevo intento",
            "answers": {"dolor_escala": 5},
        }
        second = self.client.post(self.url, second_payload, format="json")

        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", second.data)

    def test_other_patient_cannot_get_triage(self):
        TriageAssessment.objects.create(
            appointment=self.appointment,
            chief_complaint="Dolor de cabeza",
            risk_level=TriageAssessment.RiskLevel.LOW,
            risk_score=10,
            answers={"dolor_escala": 2},
        )

        self.auth_as(self.patient_other)
        res = self.client.get(self.url, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_assigned_doctor_can_patch_triage(self):
        triage = TriageAssessment.objects.create(
            appointment=self.appointment,
            chief_complaint="Dolor leve",
            risk_level=TriageAssessment.RiskLevel.LOW,
            risk_score=5,
            answers={"dolor_escala": 1},
        )

        self.auth_as(self.doctor_assigned)
        payload = {
            "chief_complaint": "Fiebre alta y dificultad respiratoria",
            "answers": {
                "fiebre": True,
                "dificultad_respiratoria": True,
                "dolor_escala": 7,
            },
        }

        res = self.client.patch(self.url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], triage.id)
        self.assertIn("risk_score", res.data)
        self.assertIn("risk_level", res.data)

    def test_other_doctor_cannot_patch_triage(self):
        TriageAssessment.objects.create(
            appointment=self.appointment,
            chief_complaint="Dolor leve",
            risk_level=TriageAssessment.RiskLevel.LOW,
            risk_score=5,
            answers={"dolor_escala": 1},
        )

        self.auth_as(self.doctor_other)
        payload = {"chief_complaint": "Intento no permitido"}

        res = self.client.patch(self.url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_clinic_can_delete_triage(self):
        TriageAssessment.objects.create(
            appointment=self.appointment,
            chief_complaint="Dolor moderado",
            risk_level=TriageAssessment.RiskLevel.MEDIUM,
            risk_score=40,
            answers={"dolor_escala": 5},
        )

        # Doctor asignado no puede borrar
        self.auth_as(self.doctor_assigned)
        res_doctor = self.client.delete(self.url)
        self.assertEqual(res_doctor.status_code, status.HTTP_403_FORBIDDEN)

        # Clinic sí puede borrar
        self.auth_as(self.clinic)
        res_clinic = self.client.delete(self.url)
        self.assertEqual(res_clinic.status_code, status.HTTP_204_NO_CONTENT)
