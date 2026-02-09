# Clínica Inteligente API
API - Plataforma Inteligente de Citas y Diagnóstico Preventivo

API REST para gestión de usuarios y citas médicas en clínicas/consultorios pequeños y medianos.  
El objetivo es reducir errores de agenda, mejorar la organización de horarios y preparar el sistema para un triaje preventivo (clasificación de riesgo) en fases futuras.

---

## Dominio: Problema que resuelve

En muchos consultorios la agenda se lleva por WhatsApp, llamadas o notas, lo que genera:
- Citas duplicadas o traslapadas
- Mala distribución de horarios
- Saturación en horas pico
- Poca trazabilidad del paciente (historial disperso)

Esta API centraliza autenticación y gestión de citas para que un frontend web/móvil pueda operar sobre una base consistente y escalable.

---

## Stack (decisiones tecnológicas)

- **Framework:** Django REST Framework (DRF)
- **Lenguaje:** Python 3.14
- **Auth:** JWT (djangorestframework-simplejwt)
- **CORS:** django-cors-headers
- **Base de datos:** SQLite3 (desarrollo local)
- **Entorno virtual:** venv (obligatorio)

**Justificación:** DRF permite construir APIs REST robustas rápidamente, con buenas prácticas de autenticación/permisos, y una arquitectura escalable por apps.

---

## Alcance (Scope) y Recursos (MVP)

### Recursos principales

1) **Auth/Users** (`accounts`)
- POST `/api/auth/register/` → registrar usuario
- POST `/api/auth/token/` → login (JWT)
- POST `/api/auth/token/refresh/` → refrescar JWT
- GET `/api/auth/me/` → obtener usuario autenticado

2) **Appointments** (`scheduling`) *(MVP planificado)*
- GET `/api/appointments/` → listar citas del usuario
- POST `/api/appointments/` → crear cita
- GET `/api/appointments/{id}/` → detalle de cita
- PATCH `/api/appointments/{id}/` → cancelar o actualizar estado

3) **Triage** (`triage`) *(planeado)*
- POST `/api/triage/` → enviar cuestionario
- GET `/api/triage/history/` → historial de cuestionarios

4) **Records** (`records`) *(planeado)*
- GET `/api/records/` → historial básico del paciente
- POST `/api/records/` → agregar registro

---

## Reglas de negocio (mínimo 5)

- Un usuario debe autenticarse con JWT para acceder a endpoints protegidos.
- No se deben exponer contraseñas en responses.
- No se puede agendar una cita en el pasado. *(MVP Scheduling)*
- Un usuario no puede tener dos citas en la misma fecha/hora. *(MVP Scheduling)*
- Una cita debe tener un estado controlado: `PENDING`, `CONFIRMED`, `CANCELLED`, `COMPLETED`. *(MVP Scheduling)*
- Solo el dueño de la cita puede verla o cancelarla. *(MVP Scheduling)*

---

## Contrato preliminar (mock)

### Endpoint 1: Registro
**POST** `/api/auth/register/`

Request:
```json
{
  "username": "paciente1",
  "email": "paciente1@mail.com",
  "password": "Password123!",
  "role": "PATIENT",
  "phone": "6640000000"
}

{
  "id": 2,
  "username": "paciente1",
  "email": "paciente1@mail.com",
  "role": "PATIENT",
  "phone": "6640000000"
}

### Endpoint 2: Login (JWT)

**POST** `/api/auth/token/`

Request:
```json

{
  "username": "paciente1",
  "password": "Password123!"
}

Response (200):
{
  "refresh": "JWT_REFRESH_TOKEN",
  "access": "JWT_ACCESS_TOKEN"
}

---

## Instalación y ejecución local (OBLIGATORIO)
1) Clonar repositorio

-git clone <URL_DEL_REPO>
-cd clinica-inteligente-api

## 2) Crear entorno virtual (venv)

-Windows (CMD/PowerShell): python -m venv .venv

## 3) Activar entorno virtual

-Windows (CMD): .venv\Scripts\activate
-Windows (PowerShell): .venv\Scripts\Activate.ps1

## 4) Instalar dependencias
- pip install -r requirements.txt

## 5) Ejecutar migraciones
- cd backend
-python manage.py migrate

## 6) Correr servidor
- python manage.py runserver
- Servidor local: http://127.0.0.1:8000/

---

