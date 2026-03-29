from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AccountsRegistrationAPITests(APITestCase):
    def setUp(self):
        self.patient_payload = {
            "username": "public_patient",
            "email": "public_patient@email.com",
            "password": "Password123!",
            "phone": "6641112233",
        }

        self.clinic = User.objects.create_user(
            username="clinic_owner",
            email="clinic_owner@email.com",
            password="Password123!",
        )
        self.clinic.role = User.Role.CLINIC
        self.clinic.save(update_fields=["role"])

        self.doctor = User.objects.create_user(
            username="doctor_user",
            email="doctor_user@email.com",
            password="Password123!",
        )
        self.doctor.role = User.Role.DOCTOR
        self.doctor.save(update_fields=["role"])

        self.patient = User.objects.create_user(
            username="patient_user",
            email="patient_user@email.com",
            password="Password123!",
        )
        self.patient.role = User.Role.PATIENT
        self.patient.save(update_fields=["role"])

    def auth_as(self, user):
        self.client.force_authenticate(user=user)

    def test_public_register_creates_patient(self):
        res = self.client.post("/api/auth/register/", self.patient_payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["role"], User.Role.PATIENT)

    def test_public_register_rejects_doctor_role(self):
        payload = {
            **self.patient_payload,
            "username": "public_doctor_attempt",
            "email": "public_doctor_attempt@email.com",
            "role": User.Role.DOCTOR,
        }

        res = self.client.post("/api/auth/register/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", res.data)

    def test_clinic_can_create_patient(self):
        self.auth_as(self.clinic)
        payload = {
            "username": "patient_created_by_clinic",
            "email": "patient_created_by_clinic@email.com",
            "password": "Password123!",
            "phone": "6641112240",
        }

        res = self.client.post("/api/auth/patients/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["role"], User.Role.PATIENT)

    def test_doctor_cannot_create_patient(self):
        self.auth_as(self.doctor)
        payload = {
            "username": "patient_created_by_doctor",
            "email": "patient_created_by_doctor@email.com",
            "password": "Password123!",
            "phone": "6641112241",
        }

        res = self.client.post("/api/auth/patients/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_cannot_create_patient(self):
        self.auth_as(self.patient)
        payload = {
            "username": "patient_created_by_patient",
            "email": "patient_created_by_patient@email.com",
            "password": "Password123!",
            "phone": "6641112242",
        }

        res = self.client.post("/api/auth/patients/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_clinic_can_create_doctor(self):
        self.auth_as(self.clinic)
        payload = {
            "username": "doctor_created_by_clinic",
            "email": "doctor_created_by_clinic@email.com",
            "password": "Password123!",
            "role": User.Role.DOCTOR,
            "phone": "6641112244",
        }

        res = self.client.post("/api/auth/staff-users/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["role"], User.Role.DOCTOR)

    def test_clinic_cannot_create_clinic(self):
        self.auth_as(self.clinic)
        payload = {
            "username": "clinic_created_by_clinic",
            "email": "clinic_created_by_clinic@email.com",
            "password": "Password123!",
            "role": User.Role.CLINIC,
            "phone": "6641112255",
        }

        res = self.client.post("/api/auth/staff-users/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", res.data)

    def test_patient_cannot_create_staff_user(self):
        self.auth_as(self.patient)
        payload = {
            "username": "doctor_created_by_patient",
            "email": "doctor_created_by_patient@email.com",
            "password": "Password123!",
            "role": User.Role.DOCTOR,
            "phone": "6641112266",
        }

        res = self.client.post("/api/auth/staff-users/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_create_staff_user(self):
        self.auth_as(self.doctor)
        payload = {
            "username": "doctor_created_by_doctor",
            "email": "doctor_created_by_doctor@email.com",
            "password": "Password123!",
            "role": User.Role.DOCTOR,
            "phone": "6641112277",
        }

        res = self.client.post("/api/auth/staff-users/", payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
