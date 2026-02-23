# Modelado del dominio — Clínica Inteligente API

## 1) Dominio (qué problema resuelve)
**Clínica Inteligente API** es una API REST para gestionar citas médicas y apoyar el diagnóstico preventivo mediante un triage básico. El problema central es común en clínicas pequeñas/medianas: saturación, citas mal distribuidas, poca estructura del historial y baja priorización de pacientes.

El sistema permite:
- Registrar usuarios (pacientes / roles básicos).
- Agendar y consultar citas (scheduling).
- Asociar servicios a una cita (detalle de la cita).
- Capturar una evaluación de riesgo (triage) para priorizar atención.
- Mantener un historial médico simple (records).

> La IA no reemplaza al médico: en MVP el triage se modela como estructura para clasificar riesgo (LOW/MEDIUM/HIGH) y almacenar respuestas.

---

## 2) Entidades y por qué existen (decisiones clave)

### User (accounts)
Entidad base para autenticación y perfiles. Se usa para identificar al paciente y a futuro separar permisos (PATIENT, STAFF/CLINIC).

### Appointment (scheduling) — Entidad principal del negocio
Representa una cita médica. Se relaciona con el usuario (paciente) y guarda fecha/hora, motivo y estado.

### Service (scheduling)
Catálogo de servicios ofrecidos (consulta general, laboratorio, etc.). Permite que una cita tenga uno o varios servicios.

### AppointmentService (scheduling) — Entidad puente (N–N)
Resuelve la relación **muchos a muchos** entre citas y servicios. Además permite guardar datos adicionales por servicio dentro de una cita:
- cantidad
- precio al reservar (price_at_booking)

### TriageAssessment (triage)
Evaluación de riesgo asociada a una cita (1–1). Guarda:
- motivo principal (chief_complaint)
- risk_level (LOW/MEDIUM/HIGH)
- risk_score
- respuestas del cuestionario (JSON)

### MedicalRecord (records)
Historial simple del paciente (notas/registro) relacionado 1–N con User.

---

## 3) Relaciones (resumen)
- **User (1) → (N) Appointment**
- **Appointment (N) ↔ (N) Service** mediante **AppointmentService**
- **Appointment (1) → (0..1) TriageAssessment**
- **User (1) → (N) MedicalRecord**

---

## 4) Reglas de integridad y restricciones (mínimas)
- Un usuario no puede tener dos citas en la misma hora:
  - `UNIQUE(patient, scheduled_at)`
- Un servicio no se repite dentro de una misma cita:
  - `UNIQUE(appointment, service)` en la tabla puente
- `scheduled_at` es obligatorio (not null).
- `Service.name` es único.
- Todas las entidades incluyen timestamps:
  - `created_at` y `updated_at`

---

## 5) Supuestos (assumptions)
- En el MVP, las citas se crean para un **paciente (User)** y no se modela aún doctor/consultorio físico.
- El triage es opcional: una cita puede existir sin evaluación hasta que el paciente responda.
- `answers` en triage se almacena en JSON para flexibilidad (preguntas pueden variar).
- `MedicalRecord` es un historial básico de notas; no sustituye un expediente clínico completo.
- En el MVP se usa SQLite para facilidad de ejecución local; se puede migrar a PostgreSQL después.

---

## 6) Archivos de diagramas
- `DER.md` 
- `UML_Clases.md`
