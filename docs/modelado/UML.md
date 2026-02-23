
---

## `docs/modelado/UML.md` (completo)

```md
# Diagrama de Clases (UML)

> Proyecto: **Clínica Inteligente API**  
> Clases del dominio (entidades), no controladores.

```mermaid
classDiagram
  class User {
    +int id
    +string username
    +string email
    +string role
    +string phone
    +datetime created_at
    +datetime updated_at
  }

  class Appointment {
    +int id
    +datetime scheduled_at
    +string reason
    +AppointmentStatus status
    +datetime created_at
    +datetime updated_at
  }

  class Service {
    +int id
    +string name
    +int duration_minutes
    +decimal base_price
    +bool is_active
    +datetime created_at
    +datetime updated_at
  }

  class AppointmentService {
    +int id
    +int quantity
    +decimal price_at_booking
    +datetime created_at
    +datetime updated_at
  }

  class TriageAssessment {
    +int id
    +string chief_complaint
    +RiskLevel risk_level
    +int risk_score
    +json answers
    +datetime created_at
    +datetime updated_at
  }

  class MedicalRecord {
    +int id
    +string title
    +text notes
    +datetime created_at
    +datetime updated_at
  }

  class AppointmentStatus {
    <<enum>>
    PENDING
    CONFIRMED
    CANCELLED
  }

  class RiskLevel {
    <<enum>>
    LOW
    MEDIUM
    HIGH
  }

  User "1" --> "0..*" Appointment : patient
  Appointment "1" --> "0..*" AppointmentService : details
  Service "1" --> "0..*" AppointmentService : services
  Appointment "1" --> "0..1" TriageAssessment : triage
  User "1" --> "0..*" MedicalRecord : records
