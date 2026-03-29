from django.core.management import call_command
from io import StringIO
from scheduling.models import AppointmentReminder

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from scheduling.models import Appointment, MedicalRecord, AppointmentReminder

from triage.models import TriageAssessment


User = get_user_model()


class SchedulingAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient_test",
            email="patient_test@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="clinic_test",
            email="clinic_test@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_patient_cannot_create_service(self):
        self.auth_as(self.patient)
        payload = {
            "name": "Servicio X",
            "base_price": "100.00",
            "duration_minutes": 30,
            "is_active": True,
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
            "is_active": True,
        }

        res = self.client.post("/api/services/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)

    def test_patient_can_create_appointment(self):
        self.auth_as(self.patient)
        future_dt = timezone.now() + timedelta(days=2)

        payload = {
            "scheduled_at": future_dt.isoformat(),
            "reason": "Consulta general",
        }

        res = self.client.post("/api/appointments/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)

    def test_patient_cannot_create_appointment_in_past(self):
        self.auth_as(self.patient)
        past_dt = timezone.now() - timedelta(days=1)

        payload = {
            "scheduled_at": past_dt.isoformat(),
            "reason": "No debe permitir",
        }

        res = self.client.post("/api/appointments/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("scheduled_at", res.data)

    def test_patient_can_reschedule_own_appointment(self):
        self.auth_as(self.patient)

        appt = Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=3),
            reason="Consulta inicial",
            status=Appointment.Status.PENDING,
        )

        url = f"/api/appointments/{appt.id}/reschedule/"
        payload = {"scheduled_at": (timezone.now() + timedelta(days=6)).isoformat()}

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("scheduled_at", res.data)

    def test_patient_cannot_reschedule_without_scheduled_at(self):
        self.auth_as(self.patient)

        appt = Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=3),
            reason="Consulta inicial",
            status=Appointment.Status.PENDING,
        )

        url = f"/api/appointments/{appt.id}/reschedule/"
        res = self.client.patch(url, {}, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_patient_cannot_reschedule_to_past(self):
        self.auth_as(self.patient)

        appt = Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=3),
            reason="Consulta inicial",
            status=Appointment.Status.PENDING,
        )

        url = f"/api/appointments/{appt.id}/reschedule/"
        payload = {"scheduled_at": (timezone.now() - timedelta(days=1)).isoformat()}

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_patient_cannot_reschedule_foreign_appointment(self):
        other_patient = User.objects.create_user(
            username="other_patient_reschedule",
            email="other_patient_reschedule@email.com",
            password="Password123!",
        )
        other_patient.role = User.Role.PATIENT
        other_patient.save(update_fields=["role"])

        appt = Appointment.objects.create(
            patient=other_patient,
            scheduled_at=timezone.now() + timedelta(days=3),
            reason="Consulta de otro paciente",
            status=Appointment.Status.PENDING,
        )

        self.auth_as(self.patient)
        url = f"/api/appointments/{appt.id}/reschedule/"
        payload = {"scheduled_at": (timezone.now() + timedelta(days=8)).isoformat()}

        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class MedicalRecordsAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient_records",
            email="patient_records@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.doctor_assigned = User.objects.create_user(
            username="doctor_assigned",
            email="doctor_assigned@email.com",
            password="Password123!",
        )
        self.doctor_assigned.role = User.Role.DOCTOR
        self.doctor_assigned.save(update_fields=["role"])

        self.doctor_other = User.objects.create_user(
            username="doctor_other",
            email="doctor_other@email.com",
            password="Password123!",
        )
        self.doctor_other.role = User.Role.DOCTOR
        self.doctor_other.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="clinic_records",
            email="clinic_records@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

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

    def test_assigned_doctor_can_patch_record(self):
        record = MedicalRecord.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_assigned,
            diagnosis="Dx inicial",
            notes="Notas iniciales",
            treatment="Tratamiento inicial",
        )

        self.auth_as(self.doctor_assigned)
        url = f"/api/appointments/{self.appointment.id}/records/{record.id}/"
        payload = {"diagnosis": "Dx actualizado", "notes": "Notas actualizadas"}

        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["diagnosis"], "Dx actualizado")

    def test_patient_cannot_patch_record(self):
        record = MedicalRecord.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_assigned,
            diagnosis="Dx inicial",
            notes="Notas iniciales",
            treatment="Tratamiento inicial",
        )

        self.auth_as(self.patient)
        url = f"/api/appointments/{self.appointment.id}/records/{record.id}/"
        res = self.client.patch(url, {"notes": "Intento no permitido"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_assigned_doctor_can_delete_record(self):
        record = MedicalRecord.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_assigned,
            diagnosis="Dx delete",
            notes="Notas delete",
            treatment="Tratamiento delete",
        )

        self.auth_as(self.doctor_assigned)
        url = f"/api/appointments/{self.appointment.id}/records/{record.id}/"

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MedicalRecord.objects.filter(id=record.id).exists())

    def test_patient_cannot_delete_record(self):
        record = MedicalRecord.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_assigned,
            diagnosis="Dx no delete",
            notes="Notas no delete",
            treatment="Tratamiento no delete",
        )

        self.auth_as(self.patient)
        url = f"/api/appointments/{self.appointment.id}/records/{record.id}/"

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class ClinicAppointmentsFilterAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="filter_patient",
            email="filter_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="filter_clinic",
            email="filter_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_clinic_can_list_all_appointments(self):
        Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=3),
            reason="Control general",
            status=Appointment.Status.PENDING,
        )

        doctor = User.objects.create_user(
            username="doctor_filter_1",
            email="doctor_filter_1@email.com",
            password="Password123!",
        )
        doctor.role = User.Role.DOCTOR
        doctor.save(update_fields=["role"])

        Appointment.objects.create(
            patient=self.patient,
            doctor=doctor,
            scheduled_at=timezone.now() + timedelta(days=4),
            reason="Consulta cardiologia",
            status=Appointment.Status.CONFIRMED,
        )

        self.auth_as(self.clinic)
        res = self.client.get("/api/clinic/appointments/", format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 2)

    def test_non_clinic_cannot_list_clinic_appointments(self):
        self.auth_as(self.patient)
        res = self.client.get("/api/clinic/appointments/", format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_filter_by_status(self):
        Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=5),
            reason="Cita pending",
            status=Appointment.Status.PENDING,
        )
        Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=6),
            reason="Cita cancelada",
            status=Appointment.Status.CANCELLED,
        )

        self.auth_as(self.clinic)
        res = self.client.get("/api/clinic/appointments/?status=PENDING", format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item["status"] == "PENDING" for item in res.data))

    def test_clinic_filter_by_doctor_and_date_range(self):
        doctor_target = User.objects.create_user(
            username="doctor_target",
            email="doctor_target@email.com",
            password="Password123!",
        )
        doctor_target.role = User.Role.DOCTOR
        doctor_target.save(update_fields=["role"])

        doctor_other = User.objects.create_user(
            username="doctor_other_filter",
            email="doctor_other_filter@email.com",
            password="Password123!",
        )
        doctor_other.role = User.Role.DOCTOR
        doctor_other.save(update_fields=["role"])

        Appointment.objects.create(
            patient=self.patient,
            doctor=doctor_target,
            scheduled_at=timezone.now() + timedelta(days=10),
            reason="Coincide filtro",
            status=Appointment.Status.CONFIRMED,
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=doctor_other,
            scheduled_at=timezone.now() + timedelta(days=10),
            reason="No coincide doctor",
            status=Appointment.Status.CONFIRMED,
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=doctor_target,
            scheduled_at=timezone.now() + timedelta(days=40),
            reason="No coincide fecha",
            status=Appointment.Status.CONFIRMED,
        )

        date_from = (timezone.now() + timedelta(days=1)).date().isoformat()
        date_to = (timezone.now() + timedelta(days=20)).date().isoformat()

        self.auth_as(self.clinic)
        url = f"/api/clinic/appointments/?doctor_id={doctor_target.id}&date_from={date_from}&date_to={date_to}"
        res = self.client.get(url, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["doctor"], doctor_target.id)


class DashboardSummaryAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="dash_patient",
            email="dash_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="dash_clinic",
            email="dash_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.doctor_1 = User.objects.create_user(
            username="dash_doctor_1",
            email="dash_doctor_1@email.com",
            password="Password123!",
        )
        self.doctor_1.role = User.Role.DOCTOR
        self.doctor_1.save(update_fields=["role"])

        self.doctor_2 = User.objects.create_user(
            username="dash_doctor_2",
            email="dash_doctor_2@email.com",
            password="Password123!",
        )
        self.doctor_2.role = User.Role.DOCTOR
        self.doctor_2.save(update_fields=["role"])

        now = timezone.now()

        self.a1 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_1,
            scheduled_at=now + timedelta(days=1),
            reason="A1",
            status=Appointment.Status.PENDING,
        )
        self.a2 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_1,
            scheduled_at=now + timedelta(days=2),
            reason="A2",
            status=Appointment.Status.CONFIRMED,
        )
        self.a3 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_1,
            scheduled_at=now + timedelta(days=3),
            reason="A3",
            status=Appointment.Status.CANCELLED,
        )
        self.a4 = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_2,
            scheduled_at=now + timedelta(days=4),
            reason="A4",
            status=Appointment.Status.COMPLETED,
        )

        TriageAssessment.objects.create(
            appointment=self.a2,
            chief_complaint="Dolor toracico",
            risk_level=TriageAssessment.RiskLevel.HIGH,
            risk_score=85,
            answers={"dolor_escala": 9},
        )

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_patient_cannot_access_dashboard_summary(self):
        self.auth_as(self.patient)
        res = self.client.get("/api/dashboard/summary/", format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_can_access_dashboard_summary_all_appointments(self):
        self.auth_as(self.clinic)
        res = self.client.get("/api/dashboard/summary/", format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["scope"], "CLINIC")
        self.assertEqual(res.data["appointments"]["total"], 4)
        self.assertEqual(res.data["appointments"]["pending"], 1)
        self.assertEqual(res.data["appointments"]["confirmed"], 1)
        self.assertEqual(res.data["appointments"]["completed"], 1)
        self.assertEqual(res.data["appointments"]["cancelled"], 1)
        self.assertEqual(res.data["triage"]["high_risk"], 1)

    def test_doctor_can_access_only_own_dashboard_summary(self):
        self.auth_as(self.doctor_1)
        res = self.client.get("/api/dashboard/summary/", format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["scope"], "DOCTOR")
        self.assertEqual(res.data["appointments"]["total"], 3)
        self.assertEqual(res.data["appointments"]["pending"], 1)
        self.assertEqual(res.data["appointments"]["confirmed"], 1)
        self.assertEqual(res.data["appointments"]["completed"], 0)
        self.assertEqual(res.data["appointments"]["cancelled"], 1)
        self.assertEqual(res.data["triage"]["high_risk"], 1)


class DashboardTrendsAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="trend_patient",
            email="trend_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="trend_clinic",
            email="trend_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.doctor_1 = User.objects.create_user(
            username="trend_doctor_1",
            email="trend_doctor_1@email.com",
            password="Password123!",
        )
        self.doctor_1.role = User.Role.DOCTOR
        self.doctor_1.save(update_fields=["role"])

        self.doctor_2 = User.objects.create_user(
            username="trend_doctor_2",
            email="trend_doctor_2@email.com",
            password="Password123!",
        )
        self.doctor_2.role = User.Role.DOCTOR
        self.doctor_2.save(update_fields=["role"])

        now = timezone.now()

        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_1,
            scheduled_at=now - timedelta(days=1),
            reason="T1",
            status=Appointment.Status.PENDING,
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_1,
            scheduled_at=now - timedelta(days=2),
            reason="T2",
            status=Appointment.Status.CONFIRMED,
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_2,
            scheduled_at=now - timedelta(days=3),
            reason="T3",
            status=Appointment.Status.CANCELLED,
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_1,
            scheduled_at=now - timedelta(days=10),
            reason="T4",
            status=Appointment.Status.COMPLETED,
        )

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_patient_cannot_access_trends(self):
        self.auth_as(self.patient)
        res = self.client.get("/api/dashboard/trends/?days=7", format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_can_access_trends_7_days(self):
        self.auth_as(self.clinic)
        res = self.client.get("/api/dashboard/trends/?days=7", format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["scope"], "CLINIC")
        self.assertEqual(res.data["days"], 7)
        self.assertEqual(len(res.data["points"]), 7)

        total_sum = sum(p["total"] for p in res.data["points"])
        self.assertEqual(total_sum, 3)

    def test_doctor_sees_only_own_trends(self):
        self.auth_as(self.doctor_1)
        res = self.client.get("/api/dashboard/trends/?days=30", format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["scope"], "DOCTOR")
        self.assertEqual(res.data["days"], 30)
        self.assertEqual(len(res.data["points"]), 30)

        total_sum = sum(p["total"] for p in res.data["points"])
        self.assertEqual(total_sum, 3)

    def test_invalid_days_returns_400(self):
        self.auth_as(self.clinic)
        res = self.client.get("/api/dashboard/trends/?days=15", format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class DoctorSchedulesAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="sched_patient",
            email="sched_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="sched_clinic",
            email="sched_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.doctor = User.objects.create_user(
            username="sched_doctor",
            email="sched_doctor@email.com",
            password="Password123!",
        )
        self.doctor.role = User.Role.DOCTOR
        self.doctor.save(update_fields=["role"])

        self.list_url = "/api/clinic/doctor-schedules/"

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_clinic_can_create_schedule(self):
        self.auth_as(self.clinic)
        payload = {
            "doctor": self.doctor.id,
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "is_active": True,
        }

        res = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["doctor"], self.doctor.id)

    def test_non_clinic_cannot_create_schedule(self):
        self.auth_as(self.patient)
        payload = {
            "doctor": self.doctor.id,
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "is_active": True,
        }

        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_create_schedule_for_non_doctor_user(self):
        self.auth_as(self.clinic)
        payload = {
            "doctor": self.patient.id,
            "day_of_week": 2,
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "is_active": True,
        }

        res = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", res.data)

    def test_clinic_can_list_schedules(self):
        self.auth_as(self.clinic)
        create_payload = {
            "doctor": self.doctor.id,
            "day_of_week": 3,
            "start_time": "08:00:00",
            "end_time": "11:00:00",
            "is_active": True,
        }
        created = self.client.post(self.list_url, create_payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        res = self.client.get(self.list_url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_clinic_can_patch_schedule(self):
        self.auth_as(self.clinic)
        create_payload = {
            "doctor": self.doctor.id,
            "day_of_week": 4,
            "start_time": "09:00:00",
            "end_time": "12:00:00",
            "is_active": True,
        }
        created = self.client.post(self.list_url, create_payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        schedule_id = created.data["id"]
        detail_url = f"/api/clinic/doctor-schedules/{schedule_id}/"

        patch_payload = {"end_time": "13:00:00"}
        res = self.client.patch(detail_url, patch_payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["end_time"], "13:00:00")

    def test_clinic_can_delete_schedule(self):
        self.auth_as(self.clinic)
        create_payload = {
            "doctor": self.doctor.id,
            "day_of_week": 5,
            "start_time": "14:00:00",
            "end_time": "18:00:00",
            "is_active": True,
        }
        created = self.client.post(self.list_url, create_payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        schedule_id = created.data["id"]
        detail_url = f"/api/clinic/doctor-schedules/{schedule_id}/"

        res = self.client.delete(detail_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

class AppointmentRemindersAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="rem_patient",
            email="rem_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="rem_clinic",
            email="rem_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=2),
            reason="Recordatorio test",
            status=Appointment.Status.PENDING,
        )

        self.base_url = f"/api/appointments/{self.appointment.id}/reminders/"

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_clinic_can_create_reminder(self):
        self.auth_as(self.clinic)
        payload = {
            "channel": "EMAIL",
            "scheduled_for": (timezone.now() + timedelta(days=1)).isoformat(),
        }

        res = self.client.post(self.base_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["appointment"], self.appointment.id)
        self.assertEqual(res.data["status"], "PENDING")

    def test_clinic_can_list_reminders(self):
        self.auth_as(self.clinic)
        payload = {
            "channel": "SMS",
            "scheduled_for": (timezone.now() + timedelta(days=1)).isoformat(),
        }
        created = self.client.post(self.base_url, payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        res = self.client.get(self.base_url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res.data), 1)

    def test_non_clinic_cannot_create_reminder(self):
        self.auth_as(self.patient)
        payload = {
            "channel": "EMAIL",
            "scheduled_for": (timezone.now() + timedelta(days=1)).isoformat(),
        }

        res = self.client.post(self.base_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_can_send_reminder(self):
        self.auth_as(self.clinic)
        payload = {
            "channel": "WHATSAPP",
            "scheduled_for": (timezone.now() + timedelta(days=1)).isoformat(),
        }
        created = self.client.post(self.base_url, payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        reminder_id = created.data["id"]
        send_url = f"/api/appointments/{self.appointment.id}/reminders/{reminder_id}/send/"

        res = self.client.post(send_url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "SENT")
        self.assertIsNotNone(res.data["sent_at"])


class TelemedicineSessionAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="tele_patient",
            email="tele_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="tele_clinic",
            email="tele_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.doctor_assigned = User.objects.create_user(
            username="tele_doctor_assigned",
            email="tele_doctor_assigned@email.com",
            password="Password123!",
        )
        self.doctor_assigned.role = User.Role.DOCTOR
        self.doctor_assigned.save(update_fields=["role"])

        self.doctor_other = User.objects.create_user(
            username="tele_doctor_other",
            email="tele_doctor_other@email.com",
            password="Password123!",
        )
        self.doctor_other.role = User.Role.DOCTOR
        self.doctor_other.save(update_fields=["role"])

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_assigned,
            scheduled_at=timezone.now() + timedelta(days=1),
            reason="Teleconsulta",
            status=Appointment.Status.CONFIRMED,
        )

        self.url = f"/api/appointments/{self.appointment.id}/telemedicine/"

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_clinic_can_create_telemedicine_session(self):
        self.auth_as(self.clinic)
        payload = {
            "meeting_url": "https://meet.example.com/abc-123",
            "access_code": "CODE123",
            "status": "SCHEDULED",
            "notes": "Sesion creada por clinic",
        }

        res = self.client.post(self.url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["appointment"], self.appointment.id)
        self.assertEqual(res.data["status"], "SCHEDULED")

    def test_assigned_doctor_can_create_telemedicine_session(self):
        self.auth_as(self.doctor_assigned)
        payload = {
            "meeting_url": "https://meet.example.com/doctor-001",
            "access_code": "DOC001",
            "status": "SCHEDULED",
            "notes": "Sesion creada por doctor",
        }

        res = self.client.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_patient_cannot_create_telemedicine_session(self):
        self.auth_as(self.patient)
        payload = {
            "meeting_url": "https://meet.example.com/patient",
            "access_code": "NOPE",
            "status": "SCHEDULED",
        }

        res = self.client.post(self.url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_can_get_session_when_exists(self):
        self.auth_as(self.clinic)
        create_payload = {
            "meeting_url": "https://meet.example.com/get-001",
            "access_code": "GET001",
            "status": "SCHEDULED",
        }
        created = self.client.post(self.url, create_payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.auth_as(self.patient)
        res = self.client.get(self.url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["meeting_url"], create_payload["meeting_url"])

    def test_other_doctor_cannot_patch_session(self):
        self.auth_as(self.clinic)
        created = self.client.post(
            self.url,
            {
                "meeting_url": "https://meet.example.com/patch-001",
                "access_code": "PATCH001",
                "status": "SCHEDULED",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.auth_as(self.doctor_other)
        res = self.client.patch(self.url, {"status": "IN_PROGRESS"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_can_patch_session(self):
        self.auth_as(self.clinic)
        created = self.client.post(
            self.url,
            {
                "meeting_url": "https://meet.example.com/patch-002",
                "access_code": "PATCH002",
                "status": "SCHEDULED",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        res = self.client.patch(
            self.url,
            {
                "status": "IN_PROGRESS",
                "started_at": (timezone.now()).isoformat(),
            },
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], "IN_PROGRESS")

class DigitalPrescriptionAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="rx_patient",
            email="rx_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.clinic = User.objects.create_user(
            username="rx_clinic",
            email="rx_clinic@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.doctor_assigned = User.objects.create_user(
            username="rx_doctor_assigned",
            email="rx_doctor_assigned@email.com",
            password="Password123!",
        )
        self.doctor_assigned.role = User.Role.DOCTOR
        self.doctor_assigned.save(update_fields=["role"])

        self.doctor_other = User.objects.create_user(
            username="rx_doctor_other",
            email="rx_doctor_other@email.com",
            password="Password123!",
        )
        self.doctor_other.role = User.Role.DOCTOR
        self.doctor_other.save(update_fields=["role"])

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor_assigned,
            scheduled_at=timezone.now() + timedelta(days=1),
            reason="Teleconsulta receta",
            status=Appointment.Status.CONFIRMED,
        )

        self.tele_url = f"/api/appointments/{self.appointment.id}/telemedicine/"

        # crear sesion de telemedicina
        self.client.force_authenticate(user=self.clinic)
        create_session = self.client.post(
            self.tele_url,
            {
                "meeting_url": "https://meet.example.com/rx-001",
                "access_code": "RX001",
                "status": "SCHEDULED",
                "notes": "Sesion para receta",
            },
            format="json",
        )
        self.session_id = create_session.data["id"]
        self.rx_url = f"/api/telemedicine/{self.session_id}/prescription/"

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_assigned_doctor_can_create_prescription(self):
        self.auth_as(self.doctor_assigned)
        payload = {
            "indications": "Tomar despues de alimentos.",
            "medications": [
                {"name": "Paracetamol", "dose": "500mg", "frequency": "cada 8h", "days": 5}
            ],
            "recommendations": "Hidratacion y reposo.",
        }

        res = self.client.post(self.rx_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)
        self.assertEqual(res.data["indications"], payload["indications"])

    def test_patient_cannot_create_prescription(self):
        self.auth_as(self.patient)
        payload = {
            "indications": "Intento no permitido",
            "medications": [{"name": "X", "dose": "1", "frequency": "1", "days": 1}],
            "recommendations": "",
        }

        res = self.client.post(self.rx_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_can_patch_prescription(self):
        self.auth_as(self.doctor_assigned)
        created = self.client.post(
            self.rx_url,
            {
                "indications": "Inicial",
                "medications": [{"name": "A", "dose": "1", "frequency": "1", "days": 1}],
                "recommendations": "Inicial",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.auth_as(self.clinic)
        res = self.client.patch(
            self.rx_url,
            {
                "recommendations": "Actualizado por clinic",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["recommendations"], "Actualizado por clinic")

    def test_patient_can_get_prescription(self):
        self.auth_as(self.doctor_assigned)
        created = self.client.post(
            self.rx_url,
            {
                "indications": "Ver por paciente",
                "medications": [{"name": "B", "dose": "2", "frequency": "2", "days": 2}],
                "recommendations": "Control",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.auth_as(self.patient)
        res = self.client.get(self.rx_url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["indications"], "Ver por paciente")

    def test_other_doctor_cannot_patch_prescription(self):
        self.auth_as(self.doctor_assigned)
        created = self.client.post(
            self.rx_url,
            {
                "indications": "Inicial",
                "medications": [{"name": "C", "dose": "3", "frequency": "3", "days": 3}],
                "recommendations": "Inicial",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.auth_as(self.doctor_other)
        res = self.client.patch(self.rx_url, {"recommendations": "No permitido"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

class ReminderCommandAPITests(APITestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="cmd_patient",
            email="cmd_patient@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            scheduled_at=timezone.now() + timedelta(days=1),
            reason="Reminder command test",
            status=Appointment.Status.PENDING,
        )

    def test_send_due_reminders_marks_email_as_sent(self):
        reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            channel=AppointmentReminder.Channel.EMAIL,
            scheduled_for=timezone.now() - timedelta(minutes=10),
            status=AppointmentReminder.Status.PENDING,
        )

        out = StringIO()
        call_command("send_due_reminders", stdout=out)

        reminder.refresh_from_db()
        self.assertEqual(reminder.status, AppointmentReminder.Status.SENT)
        self.assertIsNotNone(reminder.sent_at)
        self.assertEqual(reminder.error_message, "")

    def test_send_due_reminders_skips_future_reminders(self):
        reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            channel=AppointmentReminder.Channel.EMAIL,
            scheduled_for=timezone.now() + timedelta(hours=2),
            status=AppointmentReminder.Status.PENDING,
        )

        out = StringIO()
        call_command("send_due_reminders", stdout=out)

        reminder.refresh_from_db()
        self.assertEqual(reminder.status, AppointmentReminder.Status.PENDING)
        self.assertIsNone(reminder.sent_at)

    def test_send_due_reminders_marks_sms_as_failed(self):
        reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            channel=AppointmentReminder.Channel.SMS,
            scheduled_for=timezone.now() - timedelta(minutes=10),
            status=AppointmentReminder.Status.PENDING,
        )

        out = StringIO()
        call_command("send_due_reminders", stdout=out)

        reminder.refresh_from_db()
        self.assertEqual(reminder.status, AppointmentReminder.Status.FAILED)
        self.assertIn("aun no implementado", reminder.error_message)

    def test_send_due_reminders_marks_missing_email_as_failed(self):
        self.patient.email = ""
        self.patient.save(update_fields=["email"])

        reminder = AppointmentReminder.objects.create(
            appointment=self.appointment,
            channel=AppointmentReminder.Channel.EMAIL,
            scheduled_for=timezone.now() - timedelta(minutes=10),
            status=AppointmentReminder.Status.PENDING,
        )

        out = StringIO()
        call_command("send_due_reminders", stdout=out)

        reminder.refresh_from_db()
        self.assertEqual(reminder.status, AppointmentReminder.Status.FAILED)
        self.assertIn("no tiene email", reminder.error_message)
