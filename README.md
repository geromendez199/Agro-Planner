# Agro Planner

Agro Planner coordina la planificación agronómica con los servicios de John Deere. El backend en FastAPI sincroniza maquinaria, campos y planes de trabajo; el frontend en React ofrece un panel interactivo con mapas y formularios validados. El proyecto incorpora persistencia con SQLAlchemy, autenticación JWT con roles y métricas Prometheus para facilitar la observabilidad.

## Arquitectura

```mermaid
flowchart LR
    subgraph Client
        UI[React + Material UI]
        Map[react-leaflet Map]
    end
    subgraph Backend
        API[FastAPI REST]
        Scheduler[APScheduler]
        Metrics[prometheus-fastapi-instrumentator]
    end
    subgraph Data
        DB[(PostgreSQL/SQLite)]
        Logs[(logs/app.log)]
    end
    JD[John Deere APIs]

    UI -->|JWT| API
    Map -->|Datos geoespaciales| API
    API --> DB
    API --> Metrics
    API --> Scheduler
    Scheduler --> API
    Scheduler --> DB
    Scheduler --> JD
    API --> JD
    API --> Logs
```

## Requisitos

- Python 3.11+
- Node.js 18+
- Docker 24+ (opcional)
- Credenciales OAuth2 vigentes para John Deere

## Configuración rápida

1. **Variables de entorno**
   - Copia `.env.example` a `.env` y completa como mínimo:
     ```bash
     CLIENT_ID=tu_cliente
     CLIENT_SECRET=tu_secreto
     ORG_ID=org_jd
     JD_AUTH_URL=https://signin.johndeere.com/oauth2/token
     JD_API_BASE=https://sandboxapi.deere.com/platform
     SECRET_KEY=cambia_est0
     DB_URL=sqlite+aiosqlite:///./agroplanner.db
     ```
   - En desarrollo puedes fijar `JD_FAKE_TOKEN` para evitar llamadas reales.

2. **Backend**
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev -- --host 0.0.0.0 --port 5173
   ```
   Define `VITE_API_URL=http://localhost:8000` para que el panel apunte al backend.

4. **Contenedores**
   ```bash
   docker compose up --build
   ```
   El archivo `docker-compose.yml` levanta PostgreSQL, FastAPI y Vite con volúmenes persistentes (`./data/postgres`).

## API principal

Autenticación vía `Bearer` token (JWT). Ejemplos usando `curl`:

```bash
# Registrar primer usuario (queda como administrador)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret","role":"admin"}'

# Iniciar sesión y obtener token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret" | jq -r '.access_token')

# Crear plan de trabajo
curl -X POST http://localhost:8000/work-plans \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"field_id":"field-1","type":"SIEMBRA","start_date":"2024-01-01","end_date":"2024-01-05"}'

# Consultar métricas Prometheus
curl http://localhost:8000/metrics
```

### Endpoints destacados

| Ruta | Descripción |
| --- | --- |
| `POST /auth/register` | Registro de usuarios (solo admin una vez creado el primer usuario). |
| `POST /auth/login` | Autenticación con OAuth2 password flow, devuelve JWT. |
| `GET /machines` | Lista de máquinas almacenadas en la base de datos. |
| `GET /fields` | Campos sincronizados con John Deere. |
| `POST /work-plans` | Valida fechas ISO y crea planes locales + sincronización externa. |
| `POST /scheduler/start` | Arranca el planificador y permite ajustar intervalo en caliente. |
| `GET /john-deere/field-operations` | Proxy autenticado para operaciones de campo. |

## Sincronización automática

- `scheduler.py` ejecuta `_sync_entities` con APScheduler. Obtiene máquinas y campos en paralelo usando `asyncio.gather`, guarda los resultados con SQLAlchemy y registra cada ejecución (`last_run`, `machines_synced`, `fields_synced`).
- Se añade un job diario (06:00 AM) que consulta datos meteorológicos. Los errores se registran en `logs/app.log` mediante `logging.config.dictConfig`.
- El intervalo puede cambiarse en caliente via `POST /scheduler/interval`.

## Frontend

- **Estado global**: `MachineProvider` mantiene el catálogo de máquinas y expone `refresh` y estados de error para que otros componentes reaccionen.
- **Autenticación del panel**: guarda el JWT en `localStorage` como `agroPlannerToken` para que las peticiones incluyan la cabecera `Authorization` automáticamente.
- **Diseño**: Material UI ofrece tarjetas, formularios y loaders consistentes; `react-i18next` habilita es/en.
- **Mapa**: `react-leaflet` muestra polígonos de campos, clustering de máquinas y un trazo histórico sencillo al seleccionar una máquina.
- **Formularios**: `WorkPlanForm` valida fechas y estado antes de enviar al backend, mostrando snackbars de confirmación.

## Pruebas

- **Backend**: `pytest` + `pytest-asyncio` (ver `backend/tests/test_api.py`). Los tests se ejecutan con SQLite asincrónico y un cliente falso de John Deere.
- **Frontend**: `npm test` usa Jest y React Testing Library (`frontend/src/test`).

## Despliegue

### Railway
1. Crea un proyecto y añade dos servicios: uno para el backend (imagen Docker) y otro para Postgres gestionado por Railway.
2. Define variables en la sección *Variables* (`CLIENT_ID`, `CLIENT_SECRET`, `SECRET_KEY`, etc.) y vincula el `DB_URL` al Postgres administrado (`postgresql+asyncpg://user:pass@host:port/db`).
3. Usa secretos para inyectar el `.env` durante la build (`RAILWAY_ENVIRONMENT`).
4. Expone el puerto 8000 como servicio HTTP y configura un *Health Check* en `/metrics`.

### AWS Elastic Beanstalk
1. Empaqueta el backend con el `Dockerfile` suministrado y crea una aplicación de contenedor único.
2. Suministra un RDS PostgreSQL; añade su cadena a `DB_URL` en la consola de configuración.
3. Carga las variables sensibles como *Environment Properties* y monta un volumen `logs/` usando el archivo `.ebextensions` si quieres persistir registros.
4. Para el frontend puedes usar S3 + CloudFront subiendo el build generado por `npm run build` o desplegar el contenedor de Vite en un segundo entorno EB.

### GitHub Pages
1. Ejecuta el script de release desde la carpeta `frontend` para generar artefactos estáticos listos para Pages:
   ```bash
   cd frontend
   npm install
   npm run build:pages
   ```
   El comando crea la carpeta `docs/` en la raíz con la aplicación empaquetada y un `base` configurado para `/Agro-Planner/`.
2. Haz commit del contenido de `docs/` o deja que el workflow `Deploy frontend to GitHub Pages` lo publique automáticamente.
3. En la configuración del repositorio habilita GitHub Pages apuntando a la rama `gh-pages` (generada por el workflow) o a la carpeta `/docs` en `main` si prefieres despliegue manual.
4. Tras el primer despliegue, GitHub publicará la aplicación en `https://<tu_usuario>.github.io/Agro-Planner/`.

## Métricas y observabilidad

- `prometheus-fastapi-instrumentator` expone métricas en `/metrics` listas para Prometheus o Grafana.
- Los logs se almacenan en `logs/app.log` y en consola, facilitando la inspección durante despliegues con Docker o Railway.

## Futuras mejoras

- Integrar notificaciones push cuando el scheduler detecte inconsistencias en la flota.
- Añadir soporte para historial real de máquinas (trayectorias) mediante almacenamiento de posiciones.
- Exponer dashboards adicionales (producción vs. objetivo) reutilizando los datos persistidos en PostgreSQL.
- Automatizar despliegues con Helm Charts para Kubernetes.

## Scripts de prueba

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

---

El proyecto se entrega sin referencias a generadores automáticos y cumple PEP8/ESLint. Ajusta las credenciales antes de usarlo en producción.
