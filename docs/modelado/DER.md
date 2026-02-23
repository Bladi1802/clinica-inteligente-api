# Diagrama Entidad–Relación (DER)

> Proyecto: **Clínica Inteligente API**  
> Objetivo: representar el modelo de datos del MVP (citas, servicios, triage e historial).

```mermaid
erDiagram
    USER ||--o{ APPOINTMENT : "books"
    APPOINTMENT ||--o{ APPOINTMENT_SERVICE : "contains"
    SERVICE ||--o{ APPOINTMENT_SERVICE : "included_in"
    APPOINTMENT ||--|| TRIAGE_ASSESSMENT : "has"
    USER ||--o{ MEDICAL_RECORD : "owns"

    USER {
      int id PK
      string username "unique"
      string email "unique"
      string role
      string phone
      datetime created_at
      datetime updated_at
    }

    APPOINTMENT {
      int id PK
      int patient_id FK
      datetime scheduled_at "not null"
      string reason
      string status
      datetime created_at
      datetime updated_at
      "UNIQUE(patient_id, scheduled_at)"
    }

    SERVICE {
      int id PK
      string name "unique"
      int duration_minutes "not null"
      decimal base_price
      bool is_active
      datetime created_at
      datetime updated_at
    }

    APPOINTMENT_SERVICE {
      int id PK
      int appointment_id FK
      int service_id FK
      int quantity
      decimal price_at_booking
      datetime created_at
      datetime updated_at
      "UNIQUE(appointment_id, service_id)"
    }

    TRIAGE_ASSESSMENT {
      int id PK
      int appointment_id FK "unique"
      string chief_complaint
      string risk_level
      int risk_score
      json answers
      datetime created_at
      datetime updated_at
    }

    MEDICAL_RECORD {
      int id PK
      int patient_id FK
      string title
      text notes
      datetime created_at
      datetime updated_at
    }
