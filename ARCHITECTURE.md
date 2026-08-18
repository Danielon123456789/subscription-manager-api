# Subscription Manager — Architecture Reference

> **Propósito de este documento:** Contexto completo de la arquitectura para el asistente de código. Leer antes de escribir cualquier archivo del proyecto.

---

## 1. Visión general

Subscription Manager es una API REST para gestión personal y familiar de suscripciones digitales. Permite registrar suscripciones, programar cancelaciones, detectar suscripciones desde el correo electrónico, y recibir sugerencias inteligentes mediante un agente de IA.

**Tipo de sistema:** API REST stateless
**Patrón:** Monolito modular (Router → Service → Repository por módulo)
**Versión actual:** v1 — API pura sin frontend
**Frontend:** v2 — React o Next.js (pendiente)

---

## 2. Stack tecnológico

| Capa              | Tecnología             | Razón                                            |
| ----------------- | ----------------------- | ------------------------------------------------- |
| Backend framework | FastAPI                 | Swagger automático, Pydantic, async nativo       |
| Base de datos     | PostgreSQL              | Relacional, producción-ready                     |
| ORM               | SQLAlchemy              | Ya conocido, robusto                              |
| Migraciones       | Alembic                 | Estándar profesional para SQLAlchemy             |
| Cola de tareas    | Celery + Redis          | Worker separado, no bloquea la API                |
| Scheduler         | Celery Beat             | Tareas recurrentes (recordatorios, cancelaciones) |
| Cache / Broker    | Redis                   | Broker de Celery + cache de sesiones              |
| Agente IA         | LangChain + Groq        | Stack actual del developer                        |
| Email externo     | Gmail API + Outlook API | OAuth2 propio, gratis, sin límites               |
| Notificaciones    | SendGrid o Resend       | SMTP para emails de alerta                        |
| Contenedores      | Docker + Docker Compose | API + Worker + Postgres + Redis                   |

---

## 3. Patrón de arquitectura

### Monolito modular

Todos los módulos corren dentro del mismo proceso FastAPI pero están completamente aislados en carpetas con sus propios routers, schemas, servicios y acceso a datos.

**Ventaja:** simple de desarrollar y deployar ahora.
**Ventaja futura:** cada módulo puede extraerse como microservicio sin reescribir lógica.

### Patrón por módulo: Router → Service → Repository

```
Request HTTP
    │
    ▼
┌─────────────────────────────────────────┐
│  ROUTER (routes.py)                     │
│  - Recibe el request                    │
│  - Valida con Pydantic schemas          │
│  - Llama al service                     │
│  - Retorna la respuesta                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  SERVICE (service.py)                   │
│  - Lógica de negocio pura               │
│  - No conoce HTTP ni la DB directamente │
│  - Llama al repository                  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  REPOSITORY (repository.py)             │
│  - Único punto de acceso a la DB        │
│  - Queries SQLAlchemy                   │
│  - No contiene lógica de negocio        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
            PostgreSQL
```

**Regla importante:** un módulo nunca importa el repository de otro módulo. Si necesita datos de otro módulo, llama a su service.

---

## 4. Módulos del sistema

### 🔐 Auth

- Registro y login con email/contraseña
- JWT: access token (15 min) + refresh token (7 días)
- OAuth2 Authorization Code Flow para conectar Gmail y Outlook
- Recuperación de contraseña por email

### 📦 Subscriptions

- CRUD completo de suscripciones
- Estados: `active`, `trial`, `cancelled`, `paused`
- Cancelación inmediata o programada (`cancel_at`)
- `last_notified_at` evita emails duplicados de Celery
- Nunca se borran registros — solo se cambia el estado

### 👨‍👩‍👧 Groups

- Un usuario crea un grupo → se inserta en `group_members` con `role='owner'`
- El owner vive **únicamente** en `group_members.role` — `groups` no tiene `owner_id`
- `group_members` es la tabla pivote users ↔ groups con campo `role` y constraint `UNIQUE(group_id, user_id)`
- Roles: `owner` (ve y administra todo) / `member` (ve todas las suscripciones del grupo)
- Todos los miembros pueden ver las suscripciones de todos en el grupo
- **El owner no puede salir del grupo mientras sea owner.** Debe transferir la propiedad
  a otro miembro, o eliminar el grupo si es el único
- Soft delete vía `groups.deleted_at` — nunca `DELETE` físico

### 📧 Email Parser

Pipeline de dos fases para minimizar costo de tokens:

**Fase 1 — Filtro barato (regex, gratuito):**

- Filtrar por remitentes conocidos: `noreply@netflix.com`, `billing@spotify.com`, etc.
- Filtrar por keywords en subject: `receipt`, `invoice`, `subscription`, `cobro`, `renovación`
- Elimina ~95% del inbox sin tocar el LLM

**Fase 2 — Extracción inteligente (Groq, ~200 tokens/email):**

- Limpiar HTML, imágenes y footers del email filtrado
- Enviar solo el texto relevante a Groq
- Groq extrae: nombre del servicio, monto, moneda, fecha, ciclo de cobro
- Retornar sugerencias al usuario para confirmar — nada se guarda sin aprobación

### 🤖 AI Agent

- LangChain + Groq con tool calling
- Herramientas: `get_subscriptions`, `get_trials_expiring`, `schedule_cancellation`
- Detecta trials próximos a vencer (< 3 días)
- Programa cancelaciones automáticas al final de un trial
- Sugiere servicios con trial gratuito disponible
- Detecta suscripciones duplicadas o muy similares

### 🔔 Notifications

- Templates HTML con Jinja2
- Eventos: renovación próxima (1/3/7 días), trial por vencer (24-48 hrs), cancelación confirmada, invitación a grupo
- Días de anticipación configurables por el usuario
- v2: notificaciones in-app en tiempo real

### ⏰ Scheduler (Celery)

- `Celery Beat` ejecuta tareas recurrentes según schedule configurado
- Tarea diaria: revisar `next_billing_date` → disparar emails si aplica
- Tarea diaria: ejecutar cancelaciones donde `cancel_at` = hoy
- Tarea semanal: re-escanear correo usando `last_scanned_at`

### 📊 Dashboard

- Gasto mensual total (individual)
- Conteo por estado: activas, trials, canceladas
- Lista de próximos vencimientos (próximos 30 días)

---

## 5. Diseño de base de datos

### Tablas

| Tabla                 | Descripción                                                                |
| --------------------- | --------------------------------------------------------------------------- |
| `users`             | Usuario base. Email de registro (no el de OAuth2)                           |
| `subscriptions`     | Pertenece a un usuario via`owner_id`. Nunca se borra                      |
| `groups`            | Soft delete con`deleted_at`. El owner vive en `group_members`, no aquí |
| `group_members`     | Pivote users ↔ groups con campo`role`                                    |
| `invitations`       | Token con expiración para invitar por email                                |
| `email_connections` | Tokens OAuth2 encriptados de Gmail/Outlook. 1 usuario → muchas conexiones  |

### Decisiones clave de base de datos

- `subscriptions.owner_id` → siempre el usuario que paga, nunca el grupo
- `subscriptions.cancel_at` → campo opcional, Celery lo ejecuta diariamente
- `subscriptions.last_notified_at` → evita notificaciones duplicadas
- `email_connections` tokens encriptados con `SECRET_KEY` antes de insertar
- Nunca `DELETE` en producción — siempre cambiar `status`

---

## 6. API Endpoints

### Base URL: `/api/v1`

> **Regla REST aplicada:** cuando un recurso solo tiene sentido en el contexto de otro, va como subruta. Máximo 2 niveles de anidamiento.
> **Regla de seguridad:** `owner_id` y `user_id` SIEMPRE se extraen del JWT — nunca del body del request.

### 🔐 Auth

| Método | Endpoint                  | Auth     | Descripción                           |
| ------- | ------------------------- | -------- | -------------------------------------- |
| POST    | `/auth/register`        | público | Registro. Devuelve user + tokens       |
| POST    | `/auth/login`           | público | Login. Devuelve access + refresh token |
| POST    | `/auth/refresh`         | público | Renueva access token con refresh token |
| POST    | `/auth/forgot-password` | público | Envía email de recuperación          |
| POST    | `/auth/reset-password`  | público | Cambia contraseña con token           |
| GET     | `/auth/me`              | 🔐 JWT   | Perfil del usuario autenticado         |

### 📦 Subscriptions

| Método | Endpoint                                | Auth   | Descripción                                              |
| ------- | --------------------------------------- | ------ | --------------------------------------------------------- |
| GET     | `/subscriptions`                      | 🔐 JWT | Listar mis suscripciones (filtros: status, billing_cycle) |
| POST    | `/subscriptions`                      | 🔐 JWT | Crear suscripción.`owner_id` del JWT, nunca del body   |
| GET     | `/subscriptions/{id}`                 | 🔐 JWT | Detalle — solo si eres el owner                          |
| PATCH   | `/subscriptions/{id}`                 | 🔐 JWT | Actualización parcial (PATCH, no PUT)                    |
| DELETE  | `/subscriptions/{id}`                 | 🔐 JWT | Cancela inmediatamente (status → cancelled)              |
| POST    | `/subscriptions/{id}/schedule-cancel` | 🔐 JWT | Programa cancelación futura (body: cancel_at)            |

### 👨‍👩‍👧 Groups

| Método | Endpoint                           | Auth     | Descripción                        |
| ------- | ---------------------------------- | -------- | ----------------------------------- |
| GET     | `/groups`                        | 🔐 JWT   | Mis grupos (owner + member)         |
| POST    | `/groups`                        | 🔐 JWT   | Crear grupo.`owner_id` del JWT    |
| GET     | `/groups/{id}`                   | 🔐 JWT   | Detalle + lista de miembros         |
| GET     | `/groups/{id}/subscriptions`     | 🔐 JWT   | Suscripciones de todos los miembros |
| POST    | `/groups/{id}/invite`            | 👑 owner | Invitar por email                   |
| DELETE  | `/groups/{id}/members/{user_id}` | 👑 owner | Remover miembro                     |
| DELETE  | `/groups/{id}/leave`             | 🔐 JWT   | Salir del grupo                     |
| PATCH   | `/groups/{id}/transfer-owner`    | 👑 owner | Transfiere la propiedad a otro miembro |
| DELETE  | `/groups/{id}`                   | 👑 owner | Soft delete del grupo (`deleted_at`) |

### ✉️ Invitations

| Método | Endpoint                        | Auth     | Descripción                           |
| ------- | ------------------------------- | -------- | -------------------------------------- |
| POST    | `/invitations/{token}/accept` | público | Aceptar invitación por token de email |
| POST    | `/invitations/{token}/reject` | público | Rechazar invitación                   |

### 📧 Email Parser

| Método | Endpoint                            | Auth     | Descripción                                       |
| ------- | ----------------------------------- | -------- | -------------------------------------------------- |
| GET     | `/email/connect/gmail`            | 🔐 JWT   | Inicia OAuth2 con Google → redirect               |
| GET     | `/email/connect/gmail/callback`   | público | Callback Google → guarda tokens encriptados       |
| GET     | `/email/connect/outlook`          | 🔐 JWT   | Inicia OAuth2 con Microsoft → redirect            |
| GET     | `/email/connect/outlook/callback` | público | Callback Microsoft → guarda tokens                |
| POST    | `/email/scan`                     | 🔐 JWT   | Escanea correo → devuelve sugerencias (no guarda) |
| POST    | `/email/scan/confirm`             | 🔐 JWT   | Confirma sugerencias → guarda en subscriptions    |
| GET     | `/email/connections`              | 🔐 JWT   | Ver conexiones activas (sin tokens)                |
| DELETE  | `/email/connections/{id}`         | 🔐 JWT   | Desconectar cuenta de correo                       |

### 🤖 AI Agent

| Método | Endpoint               | Auth   | Descripción                                 |
| ------- | ---------------------- | ------ | -------------------------------------------- |
| POST    | `/agent/chat`        | 🔐 JWT | Mensaje al agente → respuesta + acciones    |
| GET     | `/agent/suggestions` | 🔐 JWT | Sugerencias proactivas sin input del usuario |

### 📊 Dashboard

| Método | Endpoint       | Auth   | Descripción                                              |
| ------- | -------------- | ------ | --------------------------------------------------------- |
| GET     | `/dashboard` | 🔐 JWT | Gasto mensual, conteos por estado, próximos vencimientos |

---

## 7. Flujos principales

### Flujo request normal

```
Cliente → HTTPS → FastAPI → JWT Middleware → Router → Service → Repository → PostgreSQL → Response
```

### Flujo tarea asíncrona (Celery)

```
Celery Beat (schedule) → Redis queue → Celery Worker → Service → PostgreSQL + SMTP
```

### Flujo email parser

```
POST /email/scan
→ OAuth2 token del usuario desde email_connections
→ Gmail/Outlook API (fetch emails)
→ Fase 1: regex filtra remitentes y subjects (~95% eliminado)
→ Fase 2: Groq extrae datos del texto limpio (~200 tokens/email)
→ Lista de suscripciones sugeridas (no guardadas)

POST /email/scan/confirm
→ Usuario aprueba sugerencias
→ Se guardan en subscriptions
```

### Flujo agente IA

```
POST /agent/chat { message: "¿tengo trials por vencer?" }
→ LangChain procesa el mensaje
→ Agent decide qué tools llamar
→ Tool: get_trials_expiring() → consulta PostgreSQL
→ LLM genera respuesta con los datos reales
→ Respuesta al usuario
```

### Flujo OAuth2 email

```
GET /email/connect/gmail
→ Redirect a Google OAuth2 consent screen
→ Usuario aprueba permisos
→ Google redirige a /email/connect/gmail/callback?code=...
→ Backend intercambia code por access_token + refresh_token
→ Tokens encriptados guardados en email_connections
```

---

## 8. Estructura de repositorios

### Repo 1: `subscription-manager-api`

```
app/
├── modules/
│   ├── auth/
│   │   ├── router.py        # FastAPI routes
│   │   ├── service.py       # Business logic
│   │   ├── repository.py    # DB queries
│   │   └── schemas.py       # Pydantic models
│   ├── subscriptions/
│   ├── groups/
│   ├── email_parser/
│   ├── agent/
│   ├── notifications/
│   └── dashboard/
├── core/
│   ├── config.py            # Settings con Pydantic BaseSettings
│   ├── database.py          # SQLAlchemy engine + session
│   └── security.py          # JWT utils, password hashing, token encryption
├── models/
│   ├── user.py
│   ├── subscription.py
│   ├── group.py
│   ├── group_member.py
│   ├── invitation.py
│   └── email_connection.py
├── tasks/
│   ├── celery_app.py        # Instancia de Celery
│   ├── renewal_tasks.py     # Revisar vencimientos diariamente
│   ├── cancel_tasks.py      # Ejecutar cancelaciones programadas
│   └── email_tasks.py       # Envío de emails
└── main.py                  # FastAPI app + routers registrados

migrations/                  # Alembic
tests/
Dockerfile
docker-compose.yml
.env.example
requirements.txt
```

### Repo 2: `subscription-manager-infra`

```
docker/
├── nginx.conf
└── Dockerfile.prod
scripts/
├── deploy.sh
└── backup_db.sh
docker-compose.prod.yml
docker-compose.dev.yml
.env.example
```

---

## 9. Servicios en Docker Compose

```yaml
services:
  api:      # FastAPI app — puerto 8000
  worker:   # Celery worker (mismo código, diferente entrypoint)
  beat:     # Celery Beat scheduler
  db:       # PostgreSQL — puerto 5432
  redis:    # Redis — puerto 6379
```

**Regla:** los servicios se comunican por nombre de servicio, nunca por `localhost`.
Ejemplo: `DATABASE_URL=postgresql://user:pass@db:5432/subscription_manager`

---

## 10. Variables de entorno

```env
# Database
DATABASE_URL=postgresql://user:password@db:5432/subscription_manager

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Groq
GROQ_API_KEY=

# Gmail OAuth2
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

# Outlook OAuth2
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_REDIRECT_URI=

# Email (SMTP)
SMTP_PROVIDER=sendgrid
SMTP_API_KEY=

# App
ENVIRONMENT=development
```

---

## 11. Decisiones de arquitectura documentadas

| #  | Decisión                             | Alternativa descartada   | Razón                                                                            |
| -- | ------------------------------------- | ------------------------ | --------------------------------------------------------------------------------- |
| 1  | Monolito modular                      | Microservicios           | Proyecto pequeño, un developer, sin justificación de complejidad operacional    |
| 2  | FastAPI                               | Flask                    | Swagger automático, Pydantic nativo, async — estándar actual para APIs Python  |
| 3  | Celery + Redis                        | APScheduler / ARQ        | Aparece en ofertas de trabajo, worker separado no bloquea la API                  |
| 4  | Regex + Groq para email               | Solo regex / Solo LLM    | Regex filtra barato (~95%), Groq solo procesa emails relevantes (~200 tokens c/u) |
| 5  | OAuth2 propio                         | Nylas (tercero)          | Gratis, sin límites, enseña OAuth2 real — diferenciador en entrevistas         |
| 6  | Frontend en v2                        | Frontend en v1           | API bien documentada es más impresionante técnicamente que un frontend básico  |
| 7 | `owner_id` solo en `group_members.role` | Duplicarlo en `groups` | **Revertido en S22.** El ahorro de JOINs era hipotético: ninguno de los 6 endpoints necesita `groups.owner_id`, y 4 requieren `group_members` de todos modos. La duplicación solo agregaba un estado inconsistente posible |frecuentes                                  |
| 8  | PATCH para actualizaciones            | PUT                      | Actualización parcial — no requiere mandar todos los campos                     |
| 9  | `last_notified_at` en subscriptions | Tabla de notificaciones  | Evita emails duplicados sin complejidad extra                                     |
| 10 | Tokens OAuth2 en DB encriptados       | Redis / memoria          | Persistencia — el usuario conecta su correo una sola vez                         |

---

## 12. Pendiente para v2

- Frontend (React o Next.js)
- Notificaciones in-app en tiempo real (WebSockets)
- Integración directa con bancos o tarjetas
- App móvil
- Exportar reportes en PDF o Excel
- Modelo SaaS con planes de pago (freemium)

---

*Documento completo al final de la fase de diseño. Siguiente paso: estructura de carpetas + primera sesión de código.*
