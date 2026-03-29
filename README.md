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
- Frontend web reiniciado desde cero con React + Vite.
- Triage y Medical Records con endpoints REST activos y probados.

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
    package.json
    src/
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
- `PATCH /api/appointments/{id}/assign-doctor/` (solo rol CLINIC)

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

- `GET /api/doctor/appointments/` (solo rol DOCTOR)
- `PATCH /api/doctor/appointments/{id}/` (solo doctor asignado)
- `PATCH /api/doctor/appointments/{id}/status/` 
-  `(solo doctor asignado, estado permitido:  COMPLETED, CANCELLED)`

### Clinic Workflow

- `GET /api/clinic/appointments/` (solo rol CLINIC)
  - Filtros opcionales:
    - `status` (`PENDING`, `CONFIRMED`, `COMPLETED`, `CANCELLED`)
    - `doctor_id`
    - `date_from` (YYYY-MM-DD)
    - `date_to` (YYYY-MM-DD)


### Medical Records

- `POST /api/appointments/{id}/records/` (solo doctor asignado)
- `GET /api/appointments/{id}/records/` (patient dueno, doctor asignado o clinic)
- `GET /api/appointments/{id}/records/{record_id}/` (patient dueno, doctor asignado o clinic)
- `PATCH /api/appointments/{id}/records/{record_id}/` (solo doctor asignado)
- `DELETE /api/appointments/{id}/records/{record_id}/` (solo doctor asignado)

### Triage

- `POST /api/appointments/{id}/triage/`
  - Permiso: patient dueño, doctor asignado o clinic
  - Crea triage (1 por cita) y calcula `risk_score` + `risk_level`

- `GET /api/appointments/{id}/triage/`
  - Permiso: patient dueño, doctor asignado o clinic
  - Consulta triage de la cita

- `PATCH /api/appointments/{id}/triage/`
  - Permiso: doctor asignado o clinic
  - Actualiza triage y recalcula `risk_score` + `risk_level`

- `DELETE /api/appointments/{id}/triage/`
  - Permiso: solo clinic
  - Elimina triage de la cita

### Dashboard

- `GET /api/dashboard/summary/`
- Permisos:
  - `CLINIC`: ve resumen global de todas las citas
  - `DOCTOR`: ve resumen solo de sus citas asignadas
  - `PATIENT`: no permitido (`403`)

### Telemedicina

#### Sesion de telemedicina por cita
- `GET /api/appointments/{id}/telemedicine/`
  - Permiso: patient dueno, doctor asignado o clinic
- `POST /api/appointments/{id}/telemedicine/`
  - Permiso: clinic o doctor asignado
- `PATCH /api/appointments/{id}/telemedicine/`
  - Permiso: clinic o doctor asignado

#### Recordatorios de cita/ Recordatorios automaticos (MVP)
- `GET /api/appointments/{id}/reminders/` (solo clinic)
- `POST /api/appointments/{id}/reminders/` (solo clinic)
- `POST /api/appointments/{id}/reminders/{reminder_id}/send/` (solo clinic, envio manual MVP)

El proyecto incluye un comando de Django para procesar recordatorios vencidos y marcarlos como enviados.

#### Ejecutar manualmente

```bash
cd backend
python manage.py send_due_reminders
```

#### Receta digital por sesion
- `GET /api/telemedicine/{session_id}/prescription/`
  - Permiso: patient dueno, doctor asignado o clinic
- `POST /api/telemedicine/{session_id}/prescription/`
  - Permiso: clinic o doctor asignado
- `PATCH /api/telemedicine/{session_id}/prescription/`
  - Permiso: clinic o doctor asignado


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
- Triage: 1 registro por cita (OneToOne), POST/GET triage: patient dueño, doctor asignado o - clinic, PATCH triage: doctor asignado o clinic, DELETE triage: solo clinic.

## Variables de entorno

El proyecto usa un archivo `.env` en la raíz para configurar entorno local y preparación para producción.

### Archivo de ejemplo
Existe un archivo `.env.example` con la plantilla base.

### Variables actuales

```bash
.env
SECRET_KEY=django-insecure-dev-only-change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=sqlite
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
```

## Notas
En desarrollo local se usa sqlite.
En producción se puede cambiar a PostgreSQL configurando DB_ENGINE=postgresql y completando credenciales.
`.env` no debe subirse al repositorio.

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
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`

Nota: el frontend usa `VITE_API_URL` si existe; si no, usa `http://127.0.0.1:8000`.

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

#### Crear record (Servicios)

`POST /api/appointments/8/records/`

```json
{
  "diagnosis": "Gastritis leve",
  "notes": "Dolor epigastrico de 3 dias",
  "treatment": "Omeprazol 20mg cada 24h por 14 dias"
}
```

#### Crear triage

`POST /api/appointments/8/triage/`

```json
{
  "chief_complaint": "Dolor toracico con falta de aire",
  "answers": {
    "fiebre": false,
    "dificultad_respiratoria": true,
    "dolor_escala": 8
  }
}
```
### Listar citas para CLINIC (con filtros)

`GET /api/clinic/appointments?status=CONFIRMED&doctor_id=3`

`GET /api/clinic/appointments?date_from=2026-03-01&date_to=2026-03-31`


### Dashboard

- `GET /api/dashboard/summary/` (roles `CLINIC` y `DOCTOR`)
- `GET /api/dashboard/trends/?days=7|30` (roles `CLINIC` y `DOCTOR`)

```json
{
  "scope": "CLINIC",
  "date": "2026-03-04",
  "appointments": {
    "total": 20,
    "pending": 5,
    "confirmed": 7,
    "completed": 6,
    "cancelled": 2,
    "today": 4
  },
  "triage": {
    "high_risk": 3
  }
}

{
  "scope": "DOCTOR",
  "days": 7,
  "points": [
    {
      "date": "2026-03-01",
      "total": 2,
      "pending": 1,
      "confirmed": 1,
      "completed": 0,
      "cancelled": 0
    },
    {
      "date": "2026-03-02",
      "total": 1,
      "pending": 0,
      "confirmed": 0,
      "completed": 1,
      "cancelled": 0
    }
  ]
}
```

### Pruebas automatizadas

```md
- Recordatorios:
  - envio de email vencido -> `SENT`
  - reminder futuro no se procesa
  - `SMS` no implementado -> `FAILED`
  - paciente sin email -> `FAILED`


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
 - `clinic lista records (200)

- Filtros de clinic appointments:
  - acceso solo CLINIC
  - filtro por status
  - filtro por doctor
  - filtro por rango de fechas

- Ejecutar pruebas de triage

```bash
python manage.py test apps.triage
```
- Cobertura actual incluye:
- restricción de segundo triage en la misma cita
- permisos GET/PATCH/DELETE por rol.

- Dashboard summary:
  - patient sin acceso (`403`)
  - clinic con resumen global (`200`)
  - doctor con resumen de sus citas (`200`)

- Dashboard trends:
  - acceso por roles (`CLINIC`/`DOCTOR` permitido, `PATIENT` bloqueado)
  - validacion de `days` (solo 7 o 30)
  - scope correcto para doctor (solo sus citas)

## Ejecucion con Docker

El backend puede ejecutarse tambien con Docker para facilitar portabilidad y despliegue local.

### Construir y levantar contenedor

```bash
docker compose up --build
```
Backend disponible en
`http://127.0.0.1:8000`

Detener contenedores
```bash
docker compose down
```

## Notas
El contenedor usa el archivo `.env` de la raiz del proyecto.
Actualmente la base de datos sigue configurada con `sqlite` para desarrollo.
El codigo se monta como volumen para reflejar cambios locales sin reconstruir todo el contenedor.

## Frontend React

El frontend fue reiniciado desde cero con React y Vite para reemplazar la version anterior en vanilla JavaScript.

### Comandos base

```bash
cd frontend
npm install
npm run dev
```

### Configuracion de API

Puedes definir la URL del backend con una variable de entorno de Vite:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Documentacion adicional

- Modelado de dominio:
- DER: `docs/modelado/DER.md`
- UML: `docs/modelado/UML.md`

## Roadmap corto

- Integrar proveedor real para recordatorios (email, SMS o WhatsApp).
- Implementar programacion automatica del comando `send_due_reminders` con Task Scheduler o Cron.
- Mejorar motor de riesgo de triage con reglas clinicas mas completas.
- Agregar frontend en React para pacientes, medicos y clinic.
- Preparar despliegue productivo con PostgreSQL, Docker y configuracion segura por entorno.
