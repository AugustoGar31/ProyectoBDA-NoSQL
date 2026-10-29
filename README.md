# NexoSQL — Plataforma Académica Interactiva y Auditoría SQL

Trabajo Práctico Integrador de **Base de Datos Aplicada**  
Carrera: Tecnicatura Universitaria en Programación / Sistemas  
Tecnologías: **MongoDB**, **FastAPI**, **Docker Compose**, **Python (PyMongo)**, **Jupyter Notebook**

---

## 1. Descripción del Proyecto

**NexoSQL** es una plataforma educativa orientada a la ejercitación práctica, auditoría y análisis de rendimiento de consultas SQL. El sistema administra el catálogo curricular de módulos temáticos con sus desafíos prácticos embebidos, registra los perfiles de los estudiantes distribuidos en comisiones horarias y persiste la telemetría detallada de cada intento de resolución (sintaxis SQL enviada, tiempo de procesamiento en milisegundos, reintentos y devoluciones pedagógicas del cuerpo docente).

El proyecto implementa una solución integral que abarca:
* Un **modelo documental** en MongoDB fundamentado a partir de los patrones de acceso del dominio.
* Una **API REST** construida con FastAPI desacoplada de la base mediante un **patrón de repositorios**.
* Garantía de **consistencia y atomicidad** sobre operaciones concurrentes críticas (`$inc`).
* Optimización de rendimiento mediante **índices estratégicos** validados con `explain("executionStats")`.
* Un **módulo analítico** en Jupyter Notebook que calcula indicadores académicos y visualizaciones de latencia.
* Despliegue reproducible orquestado en contenedores mediante **Docker Compose**.

---

## 2. Arquitectura del Sistema

La solución respeta una estricta separación de responsabilidades en capas para garantizar mantenibilidad, testeo aislado y reproducibilidad:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENTES / CONSUMIDORES                         │
│             Swagger UI (Docs)  /  JupyterLab  /  HTTP Client           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON (Puerto 8000)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               CAPA DE APLICACIÓN Y API (FastAPI) [Docker]              │
│                          src/main.py                                   │
│  - Enrutamiento RESTful (/modulos, /modulos/{id}, /inscribir)          │
│  - Validación estricta de datos de entrada/salida (Pydantic Schemas)   │
│  - Gestión de códigos de estado HTTP (200, 201, 400, 404, 422)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Tipos de datos nativos / DTOs
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      CAPA DE REPOSITORIO (PyMongo)                     │
│                       src/repository.py                                │
│  - Abstracción completa del motor NoSQL                                │
│  - Sanitización y conversión bidireccional BSON ObjectId <-> String    │
│  - Operaciones CRUD sobre la entidad principal                         │
│  - Operación atómica de negocio ($inc nativo en un solo documento)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ TCP / Protocolo MongoDB (Puerto 27017 interno)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               BASE DE DATOS DOCUMENTAL (MongoDB 7.x) [Docker]          │
│                          nexosql_db                                    │
│   ┌─────────────────────┐ ┌────────────────────┐ ┌──────────────────┐  │
│   │     modulos_sql     │ │      usuarios      │ │entregas_practicas│  │
│   └─────────────────────┘ └────────────────────┘ └──────────────────┘  │
│   Volumen persistente: mongo_data (independiente del ciclo del host)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Estructura del Repositorio

```text
Proyecto NoSQL/
├── notebooks/
│   ├── consultas.ipynb          # 10 consultas MQL obligatorias y análisis explain()
│   └── analisis.ipynb           # Pipeline de agregaciones, métricas y visualizaciones
├── src/
│   ├── main.py                  # Endpoints REST y controladores de FastAPI
│   ├── repository.py            # Capa de abstracción y persistencia en MongoDB
│   └── seed.py                  # Script automatizado e idempotente de carga inicial
├── docker-compose.yml           # Orquestación de servicios (MongoDB + API)
├── Dockerfile                   # Construcción de la imagen contenerizada de la API
├── requirements.txt             # Dependencias del backend y notebooks
├── .env.example                 # Plantilla de variables de entorno seguras
├── entrega_parcial_1.md         # Documento de Propuesta y Diseño Documental
├── entrega_parcial_2.md         # Documento de Implementación, Consultas y Rendimiento
├── entrega_parcial_3.md         # Documento de API, Repositorios y Consistencia
└── README.md                    # Manual integral del proyecto
```

---

## 4. Modelo Documental de Datos

El diseño se organiza en **3 colecciones interconectadas** que balancean documentos embebidos para lectura atómica y referencias externas para colecciones de crecimiento abierto:

```
┌───────────────────────────────────────────────┐
│                  modulos_sql                  │
├───────────────────────────────────────────────┤
│ _id: ObjectId                                 │
│ titulo: String                                │
│ dificultad: String (Baja|Media|Alta|Experto)  │
│ cantidad_inscriptos: Number                   │
│ activo: Boolean                               │
│ video_clase_url: String? [Opcional]           │
│ docente_titular: Object [Subdocumento Embebido│
│   ├── nombre, email, especialidad             │
│ ejercicios: Array<Object> [Arreglo Embebido]  │
│   └── [{ ejercicio_id, consigna, ... }]       │
└───────────────────────┬───────────────────────┘
                        │
                        │ (Referenciado en entregas y usuarios)
         ┌──────────────┴──────────────┐
         ▼                             ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│     entregas_practicas      │ │          usuarios           │
├─────────────────────────────┤ ├─────────────────────────────┤
│ _id: ObjectId               │ │ _id: ObjectId               │
│ usuario_id: ObjectId [Ref]──┼─┼─► nombre, email (único)     │
│ modulo_id: ObjectId [Ref]   │ │ comision: String            │
│ ejercicio_numero: Number    │ │ fecha_registro: ISODate     │
│ query_enviada: String       │ │ github_url: String? [Opc]   │
│ estado: String              │ │ modulos_aprobados: Array<Id>│
│ tiempo_ejecucion_ms: Number │ └─────────────────────────────┘
│ intentos: Number            │
│ fecha_entrega: ISODate      │
│ revision_docente: Obj? [Opc]│
└─────────────────────────────┘
```

### Justificación de Decisiones de Modelado (Embebidos vs. Referencias)

1. **Embebido en `modulos_sql`:**
   * **Docente Titular (1:1):** Los datos del profesor a cargo se consultan siempre de manera unificada junto con el módulo y tienen una tasa de modificación casi nula.
   * **Ejercicios (1:Pocos acotados):** Cada módulo contiene de 2 a 5 desafíos que no tienen sentido de negocio fuera del curso. Embeberlos garantiza que toda la lección se recupere en una **única lectura de disco sin costo de `JOIN`**.
2. **Referenciación en `entregas_practicas` y `usuarios`:**
   * **Relación 1:N Ilimitada:** Un alumno puede generar cientos de intentos de resolución. Embeberlos en el usuario violaría el límite físico de 16 MB de BSON y degradaría las lecturas cotidianas del perfil.
   * **Consultas Analíticas Desacopladas:** La colección `entregas_practicas` requiere ser consultada de forma masiva e independiente (promedios de latencia, estados de aprobación y auditorías docentes).

---

## 5. Guía de Instalación y Despliegue Rápido

### Requisitos Previos
* [Docker Desktop](https://www.docker.com/) instalado y corriendo en Windows/Linux/macOS.
* [Python 3.10+](https://www.python.org/) instalado localmente (para ejecución de notebooks).

### Paso 1: Clonar el Repositorio y Configurar Variables de Entorno
```bash
# Clonar el proyecto
git clone https://github.com/tu-usuario/proyecto-nosql-nexosql.git
cd "Proyecto NoSQL"

# Crear archivo de entorno a partir de la plantilla
copy .env.example .env
```

*(En Linux/macOS usar `cp .env.example .env`)*. El archivo `.env` permite definir las credenciales locales de MongoDB sin exponer contraseñas en el repositorio público.

### Paso 2: Desplegar los Servicios con Docker Compose
```bash
# Levantar el clúster (MongoDB + API FastAPI contenerizada)
docker compose up --build -d
```

Verificar que ambos contenedores se encuentren activos:
```bash
docker compose ps
```
* `nexosql_mongo`: Servicio MongoDB escuchando en el puerto local `27018`.
* `nexosql_api`: Servicio FastAPI escuchando en el puerto local `8000`.

### Paso 3: Poblado Inicial de Datos (Seed Idempotente)
Para cargar los 375 documentos representativos (5 módulos, 120 alumnos y 250 entregas):

```bash
# Crear entorno virtual local (si aún no se creó)
python -m venv venv
.\venv\Scripts\activate

# Instalar dependencias locales
pip install -r requirements.txt

# Ejecutar el script poblador
python src/seed.py
```

---

## 6. Documentación de la API REST

Una vez levantado el entorno, la documentación interactiva OpenAPI/Swagger se encuentra disponible en:
👉 **`http://localhost:8000/docs`**

### Catálogo de Endpoints

| Método | Endpoint | Código Éxito | Códigos Error | Descripción de la Operación |
| :--- | :--- | :---: | :---: | :--- |
| **GET** | `/` | `200 OK` | — | Estado del servicio y bienvenida. |
| **GET** | `/modulos` | `200 OK` | — | Lista módulos con filtros opcionales (`dificultad`, `activo`). |
| **GET** | `/modulos/{id}` | `200 OK` | `404 Not Found` | Obtiene el detalle íntegro de un módulo y sus ejercicios embebidos. |
| **POST** | `/modulos` | `201 Created` | `422 Unprocessable` | Crea un nuevo módulo educativo validado con Pydantic. |
| **PUT** | `/modulos/{id}` | `200 OK` | `404 Not Found` | Actualiza de forma atómica atributos de un módulo existente. |
| **DELETE**| `/modulos/{id}` | `200 OK` | `404 Not Found` | Elimina físicamente un módulo de la base de datos. |
| **POST** | `/modulos/{id}/inscribir` | `200 OK` | `400 Bad Request` | Inscripción concurrente con incremento atómico `$inc`. |

---

## 7. Caso de Consistencia y Atomicidad (Sección 5.6)

* **Problema de Concurrencia:** En escenarios de inscripciones simultáneas, si la aplicación lee el contador `cantidad_inscriptos`, suma 1 en memoria y sobrescribe el documento, se produce una condición de carrera (*Lost Update*) donde múltiples inscripciones concurrentes resultan en un incremento parcial erróneo.
* **Solución Implementada:** Se utilizó una **operación atómica sobre un documento único** mediante la primitiva `find_one_and_update` y el operador nativo `$inc`:
  ```python
  self.collection.find_one_and_update(
      {"_id": ObjectId(modulo_id), "activo": True},
      {"$inc": {"cantidad_inscriptos": 1}},
      return_document=ReturnDocument.AFTER
  )
  ```
* **Comportamiento ante Errores:** Si el estudiante indicado no existe en la colección `usuarios`, la capa de repositorio intercepta la operación antes de aplicar cambios, cancelando la escritura y retornando un código de error controlado `400 Bad Request` con mensaje explícito sin alterar el cupo del curso.

---

## 8. Índices y Análisis de Rendimiento con `explain()`

Para optimizar las consultas más frecuentes del sistema, se crearon los siguientes índices en el motor:

1. **`entregas_practicas` -> `{ "estado": 1 }`:** Acelera la recuperación de la cola de revisiones docentes pendientes.
2. **`modulos_sql` -> `{ "dificultad": 1 }`:** Optimiza el filtrado del catálogo de cursos.

### Resultados Comparativos de Rendimiento

| Métrica Analizada | Sin Índice (Escaneo de Colección) | Con Índice Dedicado | Impacto Observado |
| :--- | :---: | :---: | :--- |
| **Etapa de Ejecución (`stage`)** | `COLLSCAN` | `FETCH` / `IXSCAN` | Se evitó examinar la totalidad de la colección en memoria. |
| **Documentos Examinados (`totalDocsExamined`)** | **250** documentos | **37** documentos | **Reducción del 85.2% en lecturas de disco**. |
| **Ratio de Eficiencia (Examinados / Devueltos)** | 6.75 : 1 | **1 : 1** | Rendimiento óptimo (solo se leen documentos coincidentes). |

*Nota de Costo/Beneficio:* Si bien los índices incrementan ligeramente el consumo de memoria RAM y el costo en milisegundos durante escrituras masivas (`insert_many`), en este dominio el patrón es predominantemente de lectura analítica y filtrado, justificando ampliamente su adopción.

---

## 9. Módulo de Análisis de Datos (`notebooks/analisis.ipynb`)

El análisis se ejecutó directamente mediante pipelines de agregación nativos en PyMongo (`aggregate`), calculando tres indicadores clave del negocio formativo:

1. **Tasa de Aprobación Global:**
   * **56.4%** Aprobados (141 entregas).
   * **28.8%** Rechazados (72 entregas).
   * **14.8%** Pendientes de Revisión (37 entregas en cola de auditoría docente).
2. **Rendimiento Técnico y Latencias por Complejidad:**
   * Las consultas de dificultad `Media` concentran la mayor latencia promedio (**242.2 ms**) debido a que abarcan ejercicios iniciales con múltiples sentencias `JOIN` ejecutadas por alumnos en fase de prueba y error.
3. **Inercia y Progresión por Comisión:**
   * El promedio de avance es de **1.70** módulos aprobados en la Comisión Mañana y **1.43** en la Comisión Tarde.
   * Se identificaron **17 estudiantes sin ningún módulo completado** (0 aprobados), permitiendo recomendar la activación de tutorías pedagógicas tempranas.

---

## 10. Reinicialización y Limpieza del Entorno

Para restablecer el entorno a su estado original limpio desde cero:

```bash
# 1. Detener contenedores y eliminar volúmenes asociados
docker compose down -v

# 2. Reconstruir e iniciar servicios
docker compose up --build -d

# 3. Poblar la base de datos
python src/seed.py
```

---

## 11. Autores y Licencia

Proyecto desarrollado por el equipo de estudiantes de la cátedra de **Base de Datos Aplicada**.  
Código distribuido con fines exclusivamente académicos bajo licencia MIT.