# Plataforma de Planificación y Monitoreo Agrícola

Esta plataforma permite a productores y contratistas coordinar la cosecha y la siembra de forma **inteligente**, integrándose con el ecosistema digital de John Deere.  El objetivo es evitar demoras que reduzcan el rendimiento o la calidad de los cultivos, optimizar el uso de la maquinaria y tomar decisiones basadas en datos.  A continuación se describen sus características, arquitectura y forma de instalarla en un entorno de desarrollo.

## Características principales

- **Planificación dinámica de labores**: el sistema genera un calendario de cosecha y siembra optimizado para cada lote.  Tiene en cuenta la madurez del cultivo, la humedad del grano, la previsión meteorológica y la disponibilidad de maquinaria.  Las recomendaciones se envían automáticamente a la aplicación *Work Planner* de John Deere para que aparezcan en la pantalla del operador, evitando configuraciones manuales y reduciendo el riesgo de error【141785255791502†L145-L167】.  
- **Monitoreo en tiempo real**: se integran datos de telemetría de JDLink para visualizar la ubicación, horas de motor, consumo de combustible y códigos de diagnóstico de cada máquina.  Las flotas conectadas con JDLink permiten ver la localización de cada tractor o cosechadora, así como información de motor y consumo para maximizar la eficiencia y reducir tiempos muertos【524685441526289†L314-L340】.  
- **Envío y recepción de trabajos**: a través de la API *Work Plans* se transmiten planes, recomendaciones y órdenes de trabajo a las consolas de los equipos con pantallas Gen4/Gen5.  La información se presenta en la cabina y, cuando el trabajo se completa, los datos vuelven a la plataforma para análisis, asegurando registros limpios y automáticos【141785255791502†L145-L175】.  
- **Análisis de datos agronómicos**: tras cada cosecha se importan mapas de rendimiento y humedad vía *Field Operations API*.  Esto permite analizar por qué zonas del lote tuvieron menor rendimiento y ajustar la dosis de semilla o fertilizante en la próxima campaña.  
- **Arquitectura modular**: el backend está construido con **Python** y FastAPI (el lenguaje de programación más popular en 2025 según el índice TIOBE【304164759602364†L120-L128】).  El frontend está desarrollado en **React** y TypeScript para ofrecer una interfaz web moderna e intuitiva.  
- **Compatibilidad con las últimas API**: a partir de junio de 2024 John Deere unificó sus antiguas APIs de máquinas e implementos bajo la nueva **Equipment API** y actualizó el sistema de paginación de sus servicios【590711421295732†L32-L93】.  Esta aplicación utiliza los nuevos endpoints (`https://equipmentapi.deere.com/isg/`) y los parámetros de paginación `pageOffset` e `itemLimit` en lugar de los antiguos parámetros matriciales【590711421295732†L133-L170】.  Asimismo, se adapta al cambio en *Field Operations* que reemplazó el campo `product` por la lista `products` y `productTotals` por `applicationProductTotals`【590711421295732†L193-L253】.

## Estructura del repositorio

```
agro-planner/
├─ README.md              # Descripción del proyecto y guía de instalación
├─ LICENSE                # Licencia MIT
├─ .gitignore             # Archivos y carpetas a excluir del control de versiones
├─ .env.example           # Plantilla de variables de entorno
├─ codex_prompt.md        # Instrucciones para el generador automático de código (sin mencionar su nombre)
├─ backend/
│  ├─ requirements.txt     # Dependencias de Python
│  ├─ Dockerfile           # Imagen para desplegar el backend
│  └─ app/
│     ├─ __init__.py
│     ├─ main.py           # Entradas de la API REST con FastAPI
│     ├─ config.py         # Gestión de configuración mediante variables de entorno
│     ├─ john_deere_client.py  # Cliente para llamar a las APIs de John Deere
│     └─ scheduler.py       # Planificador de tareas recurrentes (APScheduler)
└─ frontend/
   ├─ package.json         # Configuración de Node y dependencias
   ├─ vite.config.ts       # Configuración de Vite para React
   ├─ tsconfig.json        # Configuración de TypeScript
   └─ src/
      ├─ main.tsx          # Punto de entrada de la aplicación React
      ├─ App.tsx           # Enrutador principal
      ├─ pages/
      │  └─ Dashboard.tsx   # Página de panel de control
      └─ components/
         ├─ MachineList.tsx # Componente que muestra las máquinas
         └─ MapView.tsx     # Componente de mapa con Leaflet
```

## Instalación

Sigue estos pasos para poner en marcha un entorno de desarrollo local:

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/agro-planner.git
   cd agro-planner
   ```

2. **Configurar variables de entorno**
   - Copia el archivo `.env.example` como `.env` y completa los valores correspondientes:
     - `CLIENT_ID` y `CLIENT_SECRET`: tus credenciales de la aplicación de John Deere.
     - `ORG_ID`: identificador de tu organización en Operations Center.
     - `JD_AUTH_URL`, `JD_API_BASE` y demás URLs: endpoints de autenticación y APIs (ver notas de actualización más abajo).
     - `DB_URL`: conexión a la base de datos (por defecto se puede usar SQLite).

3. **Instalar y ejecutar el backend**
   - Se recomienda crear un entorno virtual:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     pip install -r backend/requirements.txt
     ```
   - Ejecuta el servidor con:
     ```bash
     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend/app
     ```
   - El backend se expondrá en `http://localhost:8000`.  FastAPI genera automáticamente documentación interactiva en `/docs`.

4. **Instalar y ejecutar el frontend**
   - Requiere Node.js 18 o superior.  Entra en la carpeta del frontend y ejecuta:
     ```bash
     cd frontend
     npm install
     npm run dev
     ```
   - La aplicación React quedará disponible en `http://localhost:5173` y se comunicará con el backend a través de llamadas a `/api`.

5. **Compilación con Docker (opcional)**
   - Para desplegar el backend de forma reproducible, puedes utilizar el `Dockerfile`:
     ```bash
     cd backend
     docker build -t agro-planner-backend .
     docker run -p 8000:8000 --env-file ../.env agro-planner-backend
     ```

## Uso básico

1. **Autenticación con OAuth 2**: La plataforma obtiene un *access token* mediante tus credenciales (`CLIENT_ID` y `CLIENT_SECRET`).  Si no está configurado el token, la API intentará renovarlo automáticamente a través del endpoint de autenticación de John Deere.
2. **Visualizar máquinas**: realiza una petición GET a `/machines`.  El método utiliza la nueva **Equipment API** para listar todo el equipo de la organización usando `pageOffset` e `itemLimit` como parámetros de paginación【590711421295732†L133-L170】.
3. **Obtener lotes**: la ruta `/fields` devuelve los límites de campo almacenados en Operations Center.  Esta información es necesaria para generar planes de trabajo.  
4. **Crear un plan de trabajo**: envía un JSON a `/work-plans` con el identificador del lote, tipo de trabajo, fechas previstas y parámetros agronómicos.  La API crea un plan compatible con Work Planner y lo envía al Operations Center.  Desde allí, se sincroniza automáticamente con la pantalla de la máquina【141785255791502†L145-L175】.
5. **Sincronizar datos**: la tarea programada en `scheduler.py` consulta periódicamente la telemetría de las máquinas (JDLink) para mantener actualizados el estado y la localización【524685441526289†L314-L340】.

## Consideraciones sobre las APIs de John Deere

John Deere actualiza con frecuencia sus servicios, por lo que debes tener en cuenta los siguientes cambios importantes:

- **Unificación de máquinas e implementos**: en junio de 2024 se publicó la nueva **Equipment API**, que reemplaza a las antiguas APIs de máquinas e implementos.  Los endpoints se encuentran bajo `https://equipmentapi.deere.com/isg/` y permiten crear, listar y actualizar equipos de cualquier marca【590711421295732†L32-L93】.  A partir de enero de 2025 los endpoints antiguos empezarán a desactivarse, por lo que se recomienda migrar cuanto antes.
- **Paginación modernizada**: los parámetros matriciales `;start` y `;count` quedaron obsoletos en favor de `?pageOffset` y `?itemLimit`【590711421295732†L133-L170】.  Asimismo, la cabecera `No_Paging` se sustituyó por `x-deere-no-paging`.  Esta aplicación implementa los nuevos parámetros para compatibilizarse con los frameworks modernos.
- **Field Operations API**: la respuesta de los operaciones de campo cambió en noviembre de 2023 para incluir una lista de productos (`products`) en lugar de un único producto y un nuevo listado de totales (`applicationProductTotals`) que referencia al tanque mezclado【590711421295732†L193-L253】.  Si tu aplicación procesa mapas de aplicación, asegúrate de leer estas listas en lugar de los campos antiguos.
- **Work Planner**: esta herramienta del Operations Center, lanzada en enero de 2021, combina la planificación de cultivos con la creación de tareas utilizando líneas de guiado, límites, productos y mezclas de tanque.  Permite construir archivos de configuración a medida para las pantallas Gen4 y reducir la carga de importar todos los activos de golpe【524685441526289†L261-L307】.
- **Integración de terceros**: algunos socios como Agworld han demostrado que enviar actividades a Work Planner agiliza el trabajo de campo y genera registros automáticos【141785255791502†L145-L175】.  Esta plataforma replica ese flujo para agilizar tus labores.

## Tecnologías empleadas

- **Python / FastAPI** para el backend: elegido por su popularidad y versatilidad.  El índice TIOBE de octubre de 2025 sitúa a Python en el primer puesto entre los lenguajes de programación【304164759602364†L120-L128】.
- **React y TypeScript** para el frontend: facilitan el desarrollo de interfaces interactivas y mantienen el tipado seguro.
- **APScheduler** para la programación de tareas recurrentes.
- **Leaflet** a través de la librería `react-leaflet` para mostrar mapas de las máquinas y los lotes.
- **Docker** opcional para empaquetar el backend.

## Licencia

Este proyecto se distribuye bajo los términos de la **licencia MIT**.  Consulta el archivo [`LICENSE`](LICENSE) para más información.

---

### Notas finales

La plataforma está orientada a servir de base a un producto de agricultura de precisión.  Anímate a extenderla incorporando modelos predictivos, algoritmos de optimización de rutas o integración con otros sensores de suelo y clima.  **Evita incluir referencias al generador automático de código** en el repositorio; todo el código debe presentarse como desarrollado de forma manual y profesional.