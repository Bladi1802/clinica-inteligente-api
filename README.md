# Clinica Inteligente API

API REST para gestion de usuarios, citas medicas y servicios en clinicas/consultorios pequenos y medianos. El objetivo es reducir errores de agenda, mejorar la organización de horarios y preparar el sistema para un triaje preventivo (clasificación de riesgo) en fases futuras.

## Dominio: Problema que resuelve

En muchos consultorios la agenda se lleva por WhatsApp, llamadas o notas, lo que genera:
- Citas duplicadas o traslapadas
- Mala distribución de horarios
- Saturación en horas pico
- Poca trazabilidad del paciente (historial disperso)

Esta API centraliza autenticación y gestión de citas para que un frontend web/móvil pueda operar sobre una base consistente y escalable.

---

## Estado actual

- Backend en Django + DRF con JWT funcionando.
- Frontend web (HTML/CSS/JS) para login, registro y gestion de citas.
- Modelos de `triage` y `records` creados (sin endpoints REST activos por ahora).

## Stack

- Python 3.9 + (proyecto local con 3.14)
- Django 6.0.2
- Django REST Framework 3.16.1
- Simple JWT
- django-cors-headers
- SQLite (desarrollo)

## Estructura del proyecto

```text
clinica-inteligente-api/
  backend/
    apps/
      accounts/
      scheduling/
      triage/
      records/
    config/
    manage.py
  frontend/
    index.html
    assets/
    js/
  docs/
    modelado/
  requirements.txt
```

## Funcionalidades implementadas

### Auth y usuarios (`accounts`)

- Registro de usuario.
- Login JWT.
- Refresh de token.
- Endpoint `/me` para usuario autenticado.
- Usuario custom con roles: `PATIENT`, `DOCTOR`, `CLINIC`.

### Citas y servicios (`scheduling`)

- CRUD de citas del usuario autenticado.
- Validacion para no crear/editar citas en el pasado.
- Catalogo de servicios.
- CRUD de servicios (crear/editar/eliminar restringido a rol `CLINIC`).
- Asignar servicios a una cita (tabla puente `AppointmentService`).
- Calculo en respuesta de cita:
  - `total_duration_minutes`
  - `total_price`
- Asignacion de doctor a cita por CLINIC.
- Endpoints para DOCTOR:
 - `Listar sus citas asignadas.`
 - `Actualizar su cita asignada.`
 - `Cambiar estado a COMPLETED o CANCELLED.`
- Records medicos por cita:
 - `Crear record (solo doctor asignado).`
 - `Listar records (patient dueno, doctor asignado o clinic).`

### Dominio modelado (sin API expuesta aun)

- `triage`: modelo `TriageAssessment`.


## Endpoints activos

Base URL local backend: `http://127.0.0.1:8000`

### Auth

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/me/`

### Appointments

- `GET /api/appointments/`
- `POST /api/appointments/`
- `GET /api/appointments/{id}/`
- `PATCH /api/appointments/{id}/`
- `DELETE /api/appointments/{id}/`
- `PATCH /api/appointments/{id}/assign-doctor/ (solo rol CLINIC)`

### Services

- `GET /api/services/`
- `POST /api/services/` (solo rol `CLINIC`)
- `GET /api/services/{id}/`
- `PATCH /api/services/{id}/` (solo rol `CLINIC`)
- `DELETE /api/services/{id}/` (solo rol `CLINIC`)

### Appointment Services

- `GET /api/appointments/{id}/services/`
- `POST /api/appointments/{id}/services/`
- `PATCH /api/appointments/{id}/services/{item_id}/`
- `DELETE /api/appointments/{id}/services/{item_id}/`

### Doctor Workflow

- `GET /api/doctor/appointments/ (solo rol DOCTOR)`
- `PATCH /api/doctor/appointments/{id}/ (solo doctor asignado)`
- `PATCH /api/doctor/appointments/{id}/status/` 
-  `(solo doctor asignado, estado permitido:  COMPLETED, CANCELLED)`

### Medical Records

- `POST /api/appointments/{id}/records/ (solo doctor asignado)`
- `GET /api/appointments/{id}/records/ (patient dueno, doctor asignado o clinic)`

## Reglas de negocio actualmente en codigo

- JWT obligatorio para endpoints protegidos.
- `scheduled_at` debe ser fecha/hora futura.
- Cada servicio se puede agregar una sola vez por cita (`uniq_appointment_service`).
- Solo el dueno de la cita puede verla/editarla/eliminarla.
- Unicamente usuarios con rol `CLINIC` pueden mutar servicios.
- Solo CLINIC puede asignar doctor a una cita.
- Unicamente el doctor asignado puede actualizar su cita asignada y cambiar estado clinico.
- Solo el doctor asignado puede crear records medicos en la cita.
- Records medicos visibles por paciente dueño, doctor asignado y clinic.

## Instalacion y ejecucion local

## 1) Clonar repositorio

```bash
git clone <URL_DEL_REPO>
cd clinica-inteligente-api
```

## 2) Crear y activar entorno virtual

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3) Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4) Migraciones

```bash
cd backend
python manage.py migrate
```

## 5) Ejecutar backend

```bash
python manage.py runserver
```

Backend: `http://127.0.0.1:8000`

## 6) Ejecutar frontend

En otra terminal:

```bash
cd frontend
python -m http.server 5500
```

Frontend: `http://127.0.0.1:5500`

Nota: `frontend/js/config.js` usa por defecto `http://127.0.0.1:8000` como API base.

## Ejemplos rapidos

### Registro

`POST /api/auth/register/`

```json
{
  "username": "paciente1",
  "email": "paciente1@mail.com",
  "password": "Password123!",
  "role": "PATIENT",
  "phone": "6640000000"
}
```

### Login

`POST /api/auth/token/`

```json
{
  "username": "paciente1",
  "password": "Password123!"
}
```

### Crear cita

`POST /api/appointments/`

```json
{
  "scheduled_at": "2026-03-01T15:30:00",
  "reason": "Consulta general"
}
```

### Agregar servicio a cita

`POST /api/appointments/10/services/`

```json
{
  "service_id": 2,
  "quantity": 1
}
```

### Asignar doctor a cita (CLINIC)

`PATCH /api/appointments/10/assign-doctor/`

```json
{
  "doctor_id": 3
}
```

### Actualizar estado de cita (Solo DOCTOR asignado)

`PATCH /api/doctor/appointments/10/status/`

```json
{
  "status": "COMPLETED"
}
```

### Crear nota medica (Solo DOCTOR asignado)

`POST /api/appointments/10/records/`

```json
{
  "diagnosis": "Hipertension controlada",
  "notes": "Paciente estable, sin dolor toracico.",
  "treatment": "Losartan 50mg cada 24h"
}
```

### Pruebas automatizadas
- Ejecutar pruebas de scheduling:

```bash
python manage.py test apps.scheduling
```
- Cobertura actual incluye:
- Permisos de servicios (PATIENT bloqueado, CLINIC permitido).
- Validacion de citas en pasado.
- Flujo de records medicos:
 - `doctor asignado crea record (201)`
 - `doctor no asignado no crea (403)`
 - `patient dueno lista records (200)`
 - `clinic lista records (200)`

## Documentacion adicional

- Modelado de dominio: `README.md`
- DER: `docs/modelado/DER.md`
- UML: `docs/modelado/UML.md`

## Roadmap corto

- Exponer endpoints REST para `triage`.
- Agregar detalle/edicion de records medicos `(GET/PATCH por record).`
- Agregar filtros por estado/doctor/fecha para citas.
- Preparar configuracion para entorno de produccion (variables de entorno y DB externa).
