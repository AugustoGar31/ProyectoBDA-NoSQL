# TRABAJO PRÁCTICO INTEGRADOR — BASE DE DATOS APLICADA

## Entrega Parcial 4: Módulo de Análisis de Datos, Integración con Docker Compose y Entorno Limpio

### Metadatos del Proyecto

* **Proyecto:** NexoSQL — Plataforma Académica Interactiva para el Aprendizaje y Auditoría de SQL
* **Base de Datos:** `nexosql_db`
* **Tecnologías:** MongoDB 7.x, FastAPI, Docker Compose, PyMongo, Matplotlib
* **Entregables Vinculados:** `notebooks/analisis.ipynb`, `Dockerfile`, `docker-compose.yml`, `.env.example`

---

## 1. Módulo de Análisis de Datos (Requerimiento 5.7)

### 1.1. Estrategia Técnica y Extracción
En lugar de procesar los datos de forma aislada en memoria externa, el módulo de análisis implementado en `notebooks/analisis.ipynb` aprovecha la potencia de cálculo distribuido del **motor de agregación nativo de MongoDB** (`db.collection.aggregate()`). Esta estrategia garantiza que las etapas de filtrado, cruce referencial y cálculo estadístico se resuelvan directamente en el motor de base de datos antes de retornar los conjuntos consolidados a Python para su graficación.

---

### 1.2. Indicador 1: Tasa de Aprobación y Distribución de Estados de Entrega

* **Objetivo de Negocio:** Evaluar el porcentaje de asimilación conceptual de los estudiantes y cuantificar el backlog de revisiones manuales asignadas a los docentes.
* **Pipeline MQL / PyMongo Implementado:**
  ```python
  pipeline_indicador_1 = [
      {
          "$group": {
              "_id": "$estado",
              "cantidad": {"$sum": 1}
          }
      }
  ]
  ```
* **Métricas Reales Obtenidas (Universo: 250 entregas):**

  | Estado de la Entrega | Cantidad Absoluta | Proporción (%) | Interpretación Operativa |
  | :--- | :---: | :---: | :--- |
  | **Aprobado** | 141 | 56.4% | Consultas SQL correctas que superaron las pruebas automáticas o manuales. |
  | **Rechazado** | 72 | 28.8% | Soluciones con fallos sintácticos, timeout o resultados no coincidentes. |
  | **Pendiente_Revision** | 37 | 14.8% | Entregas que demandan auditoría humana y calificación cualitativa docente. |

---

### 1.3. Indicador 2: Rendimiento Técnico (Latencia en ms por Complejidad del Módulo)

* **Objetivo de Negocio:** Analizar la carga computacional generada por las consultas de los estudiantes sobre el motor de base de datos, desglosada por nivel didáctico.
* **Pipeline MQL / PyMongo Implementado:**
  Aplica un cruce referencial desacoplado mediante `$lookup` y posterior desempaquetado con `$unwind`:
  ```python
  pipeline_indicador_2 = [
      {
          "$lookup": {
              "from": "modulos_sql",
              "localField": "modulo_id",
              "foreignField": "_id",
              "as": "modulo"
          }
      },
      {"$unwind": "$modulo"},
      {
          "$group": {
              "_id": "$modulo.dificultad",
              "promedio_ms": {"$avg": "$tiempo_ejecucion_ms"},
              "min_ms": {"$min": "$tiempo_ejecucion_ms"},
              "max_ms": {"$max": "$tiempo_ejecucion_ms"},
              "total_consultas": {"$sum": 1}
          }
      }
  ]
  ```
* **Métricas Reales Obtenidas:**

  | Dificultad | Consultas Evaluadas | Latencia Promedio | Latencia Mínima | Latencia Máxima |
  | :--- | :---: | :---: | :---: | :---: |
  | **Baja** | 53 | 217.6 ms | 7 ms | 438 ms |
  | **Media** | 99 | **242.2 ms** | 5 ms | 449 ms |
  | **Alta** | 56 | 234.4 ms | 16 ms | 422 ms |
  | **Experto** | 42 | 232.5 ms | 21 ms | 446 ms |

* **Hallazgo:** El nivel **Media** concentra tanto la mayor cantidad de transacciones (99 envíos, casi el 40% del sistema) como la latencia promedio más elevada ($242.2\text{ ms}$). Esto se debe a que introduce agrupamientos y joins complejos que los alumnos ejecutan reiteradamente sin optimizar sus índices.

---

### 1.4. Indicador 3: Progresión Estudiantil y Diagnóstico de Deserción por Comisión

* **Objetivo de Negocio:** Medir la tasa de avance curricular por franja horaria e identificar a los estudiantes en situación de inercia o riesgo de abandono.
* **Pipeline MQL / PyMongo Implementado:**
  Utiliza `$project` con el operador `$size` sobre el arreglo de módulos aprobados y un condicional acumulador con `$cond`:
  ```python
  pipeline_indicador_3 = [
      {
          "$project": {
              "comision": 1,
              "cant_aprobados": {"$size": "$modulos_aprobados"}
          }
      },
      {
          "$group": {
              "_id": "$comision",
              "alumnos_totales": {"$sum": 1},
              "promedio_modulos_aprobados": {"$avg": "$cant_aprobados"},
              "sin_avance": {
                  "$sum": {"$cond": [{"$eq": ["$cant_aprobados", 0]}, 1, 0]}
              }
          }
      }
  ]
  ```
* **Métricas Reales Obtenidas:**

  | Comisión Horaria | Alumnos Totales | Promedio Módulos Aprobados | Alumnos sin Avance (0 Aprobados) | Tasa de Inercia (%) |
  | :--- | :---: | :---: | :---: | :---: |
  | **Comisión Mañana** | 46 | 1.70 | 8 | 17.4% |
  | **Comisión Tarde** | 42 | 1.43 | 9 | 21.4% |
  | **Comisión Noche** | 32 | 1.56 | 6 | 18.7% |
  | **Totales / Promedio** | **120** | **1.57** | **23** | **19.2%** |

---

### 1.5. Visualizaciones Gráficas (Generadas con Matplotlib)

En el notebook `notebooks/analisis.ipynb` se generó una figura unificada (`14x5` pulgadas) compuesta por dos gráficos contrastados:

1. **Visualización 1 (Gráfico de Dona):**
   * Muestra la proporción porcentual de los estados de entrega: **56.4% Aprobado (Verde)**, **28.8% Rechazado (Rojo)** y **14.8% Pendiente_Revision (Naranja)**.
   * Permite constatar a simple vista que la plataforma mantiene un flujo mayoritario de resolución exitosa pero con una demanda persistente de revisión humana.
2. **Visualización 2 (Gráfico de Barras con Anotación Numérica):**
   * Compara los tiempos de ejecución promedio en milisegundos a través de los cuatro niveles de complejidad: Baja ($217.6\text{ ms}$), Media ($242.2\text{ ms}$), Alta ($234.4\text{ ms}$) y Experto ($232.5\text{ ms}$).
   * Cada barra cuenta con su valor explicitado en la parte superior para facilitar la lectura inmediata.

---

### 1.6. Interpretación Pedagógica y Toma de Decisiones

1. **Gestión del Backlog Docente (Indicador 1):**  
   Las 37 entregas en estado `Pendiente_Revision` requieren intervención activa. Se recomienda implementar una regla de balanceo en la API que distribuya equitativamente los envíos pendientes entre los docentes según el módulo correspondiente, fijando un SLA máximo de 48 horas para evitar el desánimo del estudiante.
2. **Optimización Temprana en Módulos Intermedios (Indicador 2):**  
   Dado que el nivel `Media` registra la mayor latencia promedio ($242.2\text{ ms}$), se propone incorporar en dicho módulo ejercicios guiados de análisis con `EXPLAIN` antes de permitir entregas complejas con agrupamientos masivos.
3. **Plan de Contención contra el Abandono (Indicador 3):**  
   Se detectó que 23 de los 120 estudiantes registrados (19.2%) mantienen su historial de aprobaciones en cero. Se sugiere configurar una alerta automática en la plataforma que notifique a los tutores cuando un alumno supere los 10 días desde su registro sin haber alcanzado su primera aprobación.

---

## 2. Integración y Despliegue con Docker Compose (Requerimiento 5.8)

El sistema implementa una arquitectura multicontenedor completamente integrada mediante **Docker Compose**, vinculando el motor de base de datos con la API REST a través de una red interna bridge aislada.

```
                  ┌────────────────────────────────────────┐
                  │              HOST LOCAL                │
                  │   Navegador Web / Swagger / PyMongo    │
                  └──────┬──────────────────────────┬──────┘
                         │                          │
           Puerto 8000:8000                         │ Puerto 27018:27017
                         ▼                          ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   RED DOCKER: nexosql_network                          │
│                                                                        │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐   │
│   │   Servicio API (FastAPI)    │    │    Servicio Base (Mongo)    │   │
│   │    Contenedor: nexosql_api  │    │   Contenedor: nexosql_mongo │   │
│   │                             │    │                             │   │
│   │   Uvicorn (puerto 8000)     │───►│   MongoDB 7.x (puerto 27017)│   │
│   │   URI: mongodb:27017        │    │   Volumen: mongo_data       │   │
│   └─────────────────────────────┘    └─────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Configuración de Servicios (`docker-compose.yml`)

* **Servicio `mongodb`:**
  * Imagen base oficial `mongo:latest`.
  * Nombre de contenedor: `nexosql_mongo`.
  * Redirección de puertos: `27018:27017` (hacia el host local).
  * Persistencia garantizada mediante volumen nombrado `mongo_data` mapeado a `/data/db`.
* **Servicio `api`:**
  * Construcción dinámica mediante `Dockerfile` contextual (`build: .`).
  * Nombre de contenedor: `nexosql_api`.
  * Redirección de puertos: `8000:8000`.
  * Dependencia explícita (`depends_on: [mongodb]`).
  * Inyección de la variable de entorno `MONGO_URI` apuntando al host interno del servicio (`mongodb:27017`) y no a `localhost`.

### 2.2. Empaquetado del Backend (`Dockerfile`)

Se diseñó una imagen liviana basada en `python:3.11-slim`, garantizando un despliegue seguro y con mínimo consumo de memoria:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/main.py .
COPY src/repository.py .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.3. Gestión Segura de Credenciales (`.env` y `.env.example`)

Conforme a las exigencias de seguridad de la cátedra, el repositorio no incluye contraseñas ni secretos hardcodeados. Se proporciona el archivo de plantilla `.env.example`:

```env
# Credenciales de administración para MongoDB
MONGO_USER=tu_usuario_aqui
MONGO_PASS=tu_contrasena_aqui

# Puertos expuestos en el entorno host
MONGO_PORT=27018
API_PORT=8000
```

---

## 3. Protocolo de Ejecución y Validación en Entorno Limpio

Para certificar la reproducibilidad absoluta de la solución desde cero (criterio obligatorio evaluado con 10 puntos), se validó el siguiente procedimiento:

```powershell
# 1. Detener cualquier instancia previa y purgar volúmenes residuales (-v)
docker compose down -v

# 2. Compilar la imagen de la API y levantar los servicios en segundo plano
docker compose up --build -d

# 3. Verificar que ambos contenedores se encuentren en estado 'Up'
docker compose ps

# 4. Poblar la base de datos de manera reproducible con el seed idempotente
python src/seed.py

# 5. Comprobar la respuesta de la API y de la base documental
# Acceder en el navegador a: http://localhost:8000/docs
# Ejecutar GET /modulos y verificar retorno de código 200 OK con los 5 módulos cargados
```

---

## 4. Estado Final del Proyecto

Con la concreción de esta cuarta fase, el proyecto **NexoSQL** reúne:
* **Base de Datos Documental:** 3 colecciones operativas (`modulos_sql`, `usuarios`, `entregas_practicas`) con 375 documentos y relaciones justificadas.
* **Optimización e Índices:** Índices específicos que redujeron las lecturas de disco de 250 a 37 documentos examinados (verificado mediante `explain()`).
* **API y Repositorios:** Arquitectura desacoplada en capas, validación con Pydantic, respuestas HTTP RESTful y garantía de consistencia atómica mediante `$inc`.
* **Análisis Estadístico:** Indicadores calculados nativamente en MongoDB y visualizados en Jupyter Notebook.
* **Infraestructura Contenerizada:** Orquestación total en Docker Compose verificada en entorno limpio.