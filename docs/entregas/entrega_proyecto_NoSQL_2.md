# TRABAJO PRÁCTICO INTEGRADOR — BASE DE DATOS APLICADA

## Entrega Parcial 2: Implementación, Carga de Datos, Consultas Avanzadas y Rendimiento

### Metadatos del Proyecto
* **Proyecto:** NexoSQL — Plataforma Académica Interactiva para el Aprendizaje y Auditoría de SQL
* **Base de Datos:** `nexosql_db`
* **Entorno:** MongoDB 7.x (Docker Compose), Python 3.x (PyMongo, Faker, Pandas), Jupyter Notebook (`notebooks/consultas.ipynb`)
* **Colecciones Activas:** `modulos_sql`, `usuarios`, `entregas_practicas`

---

## 1. Implementación y Carga de Datos (Requerimiento 5.2)

### 1.1. Estrategia de Carga y Reproducibilidad
Para cumplir con los criterios de reproducibilidad y evaluación limpia del sistema, la persistencia inicial no se realiza mediante inserciones manuales, sino a través de un script automatizado (`seed.py`). 

El script aplica las siguientes directivas:
1. **Idempotencia:** Al inicio de su ejecución, elimina las colecciones previas (`db.coleccion.drop()`) para garantizar que sucesivas corridas de prueba inicien siempre desde un estado limpio y predecible.
2. **Volumen Representativo:** Supera ampliamente el umbral exigido por la cátedra (mínimo de 100 registros), distribuyendo el volumen según la frecuencia transaccional real del dominio académico.
3. **Casos Límite y Variabilidad:**
   * **Atributos opcionales:** Módulos con y sin `video_clase_url`; usuarios con y sin perfil `github_url`; entregas con y sin subdocumento `revision_docente`.
   * **Casos límite:** Estudiantes recién inscriptos con la lista `modulos_aprobados` vacía (`$size: 0`).
   * **Estados y dispersión:** Entregas clasificadas en estados `Aprobado`, `Rechazado` y `Pendiente_Revision`, con tiempos de ejecución que varían entre 5 ms y 450 ms y contadores de intentos acumulativos.

### 1.2. Verificación de Volúmenes Cargados
Tras la ejecución de `python src\seed.py`, el recuento efectivo de documentos persistidos en la base `nexosql_db` es el siguiente:

| Colección | Cantidad de Documentos | Justificación de Volumen |
| :--- | :---: | :--- |
| `modulos_sql` | **5** | Catálogo estructurado de unidades curriculares (Select, Joins, Agrupaciones, Subconsultas/CTEs y Optimización), conteniendo de 2 a 4 ejercicios embebidos cada una (total: 16 ejercicios prácticos). |
| `usuarios` | **120** | Muestra de estudiantes distribuidos equitativamente entre las comisiones Mañana, Tarde y Noche, con niveles heterogéneos de avance curricular. |
| `entregas_practicas` | **250** | Historial de telemetría y auditoría de consultas SQL enviadas por los alumnos para su validación computacional y pedagógica. |
| **Total Global** | **375** | **Supera el rango sugerido de 200 a 500 documentos.** |

### 1.3. Procedimiento para Reinicializar el Entorno
Para reconstruir la base de datos desde cero en cualquier máquina:
```bash
# 1. Asegurar la ejecución del contenedor MongoDB
docker compose up -d

# 2. Activar el entorno virtual de Python
.\venv\Scripts\activate

# 3. Ejecutar el script poblador
python src\seed.py
```

---

## 2. Catálogo de Consultas MongoDB (Requerimiento 5.3)

A continuación se detallan las 10 consultas implementadas en el archivo `notebooks/consultas.ipynb`, diseñadas para responder a problemáticas reales de gestión didáctica y auditoría técnica de NexoSQL.

---

### Requerimiento 1: Filtros y Operadores de Comparación

#### Consulta 1: Módulos de Complejidad Avanzada
* **Objetivo de Negocio:** Filtrar aquellos cursos de nivel elevado para coordinar clases de apoyo sincrónicas con los docentes titulares.
* **Operador Principal:** `$in`
* **Comando MQL / PyMongo:**
```python
db.modulos_sql.find(
    {"dificultad": {"$in": ["Alta", "Experto"]}},
    {"titulo": 1, "dificultad": 1, "cantidad_inscriptos": 1, "_id": 0}
)
```
* **Resultado Obtenido / Esperado:**
```text
• Subconsultas y CTEs | Dificultad: Alta | Inscriptos: 38
• Optimización, Índices y Transacciones | Dificultad: Experto | Inscriptos: 48
```

#### Consulta 2: Detección de Consultas Lentas
* **Objetivo de Negocio:** Identificar sentencias SQL enviadas por estudiantes que excedieron un umbral de 250 ms, señalando potenciales consultas ineficientes o cuellos de botella en la sintaxis.
* **Operador Principal:** `$gt`
* **Comando MQL / PyMongo:**
```python
db.entregas_practicas.find(
    {"tiempo_ejecucion_ms": {"$gt": 250}},
    {"query_enviada": 1, "tiempo_ejecucion_ms": 1, "estado": 1, "_id": 0}
).limit(3)
```
* **Resultado Obtenido / Esperado:**
```text
• [Rechazado] 384 ms -> Query: SELECT dept_id, AVG(salario) FROM empleados GROUP BY dept_id HAVING AVG(salario) > 5000;
• [Aprobado] 312 ms -> Query: WITH ventas_anuales AS (...) SELECT * FROM ventas_anuales WHERE total > 10000;
• [Pendiente_Revision] 410 ms -> Query: CREATE INDEX idx_cliente_fecha ON facturas(cliente_id, fecha_emision);
```

---

### Requerimiento 2: Operadores Lógicos

#### Consulta 3: Identificación de Entregas Críticas
* **Objetivo de Negocio:** Construir la cola de atención prioritaria para el docente, compuesta por entregas que requieren revisión manual obligatoria (`Pendiente_Revision`) o entregas reiteradamente rechazadas con más de 3 intentos fallidos.
* **Operador Principal:** `$or` (con evaluación relacional interna)
* **Comando MQL / PyMongo:**
```python
db.entregas_practicas.find({
    "$or": [
        {"estado": "Pendiente_Revision"},
        {"estado": "Rechazado", "intentos": {"$gt": 3}}
    ]
}, {"estado": 1, "intentos": 1, "tiempo_ejecucion_ms": 1, "_id": 0})
```
* **Resultado Obtenido / Esperado:**
Recupera el subconjunto de documentos que cumplen cualquiera de las dos condiciones operativas, permitiendo cuantificar la carga de soporte pedagógico urgente requerida.

---

### Requerimiento 3: Atributos Anidados

#### Consulta 4: Entregas con Devolución Docente Sobresaliente
* **Objetivo de Negocio:** Auditar el feedback cualitativo emitido por los profesores titulares en resoluciones que obtuvieron calificación destacada ($\ge 9$) dentro del objeto anidado `revision_docente`.
* **Atributo Anidado:** `revision_docente.calificacion_manual`
* **Comando MQL / PyMongo:**
```python
db.entregas_practicas.find(
    {"revision_docente.calificacion_manual": {"$gte": 9}},
    {
        "query_enviada": 1,
        "revision_docente.calificacion_manual": 1,
        "revision_docente.comentario": 1,
        "_id": 0
    }
).limit(2)
```
* **Resultado Obtenido / Esperado:**
```text
• Nota: 10 | Feedback: Excelente uso de índices compuestos, muy buen tiempo de respuesta.
• Nota: 9  | Feedback: Muy buena resolución aplicando CTEs para mejorar la legibilidad.
```

---

### Requerimiento 4: Arreglos o Listas

#### Consulta 5: Estudiantes sin Avance Curricular (Caso Límite)
* **Objetivo de Negocio:** Segmentar a los alumnos que registran cero módulos completados en su lista de aprobaciones para activar campañas de retención estudiantil.
* **Operador Principal:** `$size` sobre el arreglo `modulos_aprobados`
* **Comando MQL / PyMongo:**
```python
db.usuarios.find(
    {"modulos_aprobados": {"$size": 0}},
    {"nombre": 1, "comision": 1, "email": 1, "_id": 0}
)
```
* **Resultado Obtenido / Esperado:**
Devuelve los registros que presentan `modulos_aprobados: []`. En la muestra generada, representa aproximadamente el 20-25% del total de usuarios dados de alta.

---

### Requerimiento 5: Proyección, Ordenamiento y Límite

#### Consulta 6: Últimos Ingresos Estudiantiles por Comisión
* **Objetivo de Negocio:** Obtener los 5 alumnos más recientemente matriculados en la plataforma, omitiendo identificadores internos del motor y ordenando de forma descendente por marca temporal.
* **Operaciones:** Proyección explícita, `.sort()` y `.limit()`
* **Comando MQL / PyMongo:**
```python
db.usuarios.find(
    {},
    {"nombre": 1, "comision": 1, "fecha_registro": 1, "_id": 0}
).sort("fecha_registro", -1).limit(5)
```
* **Resultado Obtenido / Esperado:**
```text
• Martín Benítez  | Comisión Noche  | Fecha: 2026-10-18
• Sofía Herrera   | Comisión Mañana | Fecha: 2026-10-14
• Lucas Almada    | Comisión Tarde  | Fecha: 2026-10-09
• Camila Duarte   | Comisión Noche  | Fecha: 2026-09-30
• Julián Morales  | Comisión Mañana | Fecha: 2026-09-22
```

---

### Requerimiento 6: Pipelines de Agregación (`aggregate()`)

#### Consulta 7: Cómputo de Puntaje Máximo por Módulo (`$unwind` + `$group`)
* **Objetivo de Negocio:** Desanidar el arreglo de ejercicios embebidos dentro de cada curso y calcular de forma agregada el puntaje acumulado total que un estudiante puede obtener al completar el temario.
* **Etapas del Pipeline:** `$unwind` $\to$ `$group` $\to$ `$sort`
* **Comando MQL / PyMongo:**
```python
pipeline_puntajes = [
    {"$unwind": "$ejercicios"},
    {
        "$group": {
            "_id": "$titulo",
            "dificultad": {"$first": "$dificultad"},
            "total_puntos": {"$sum": "$ejercicios.puntaje"},
            "ejercicios_totales": {"$sum": 1}
        }
    },
    {"$sort": {"total_puntos": -1}}
]
db.modulos_sql.aggregate(pipeline_puntajes)
```
* **Resultado Obtenido / Esperado:**
```text
• Optimización, Índices y Transacciones (Experto): 120 pts en 3 ejercicios
• Subconsultas y CTEs (Alta): 90 pts en 4 ejercicios
• Joins (Inner, Left, Right) (Media): 60 pts en 3 ejercicios
• Funciones de Agregación y Group By (Media): 50 pts en 2 ejercicios
• Select Básico y Filtrado (Baja): 40 pts en 2 ejercicios
```

#### Consulta 8: Cruce Transversal de Entregas y Alumnos (`$lookup`)
* **Objetivo de Negocio:** Enlazar la colección desacoplada `entregas_practicas` con `usuarios` mediante `$lookup` para conocer el nombre y comisión de quienes tienen entregas pendientes de resolución, sin desnormalizar el modelo base.
* **Etapas del Pipeline:** `$match` $\to$ `$lookup` $\to$ `$unwind` $\to$ `$project` $\to$ `$limit`
* **Comando MQL / PyMongo:**
```python
pipeline_cruce = [
    {"$match": {"estado": "Pendiente_Revision"}},
    {
        "$lookup": {
            "from": "usuarios",
            "localField": "usuario_id",
            "foreignField": "_id",
            "as": "estudiante"
        }
    },
    {"$unwind": "$estudiante"},
    {
        "$project": {
            "_id": 0,
            "estudiante": "$estudiante.nombre",
            "comision": "$estudiante.comision",
            "intentos": "$intentos",
            "query": "$query_enviada"
        }
    },
    {"$limit": 3}
]
db.entregas_practicas.aggregate(pipeline_cruce)
```
* **Resultado Obtenido / Esperado:**
Genera un conjunto unificado que correlaciona el código SQL pendiente con los datos filiatorios del alumno emisor.

---

### Requerimiento 7: Agrupamiento y Cálculos Estadísticos

#### Consulta 9: Telemetría de Latencia según Estado de Entrega
* **Objetivo de Negocio:** Obtener indicadores de dispersión y rendimiento sobre las consultas enviadas, calculando promedio, mínimo y máximo en milisegundos para contrastar soluciones aprobadas contra rechazadas.
* **Operadores Estadísticos:** `$avg`, `$min`, `$max`, `$sum`
* **Comando MQL / PyMongo:**
```python
pipeline_estadisticas = [
    {
        "$group": {
            "_id": "$estado",
            "total_muestras": {"$sum": 1},
            "tiempo_promedio_ms": {"$avg": "$tiempo_ejecucion_ms"},
            "latencia_minima_ms": {"$min": "$tiempo_ejecucion_ms"},
            "latencia_maxima_ms": {"$max": "$tiempo_ejecucion_ms"}
        }
    },
    {"$sort": {"total_muestras": -1}}
]
db.entregas_practicas.aggregate(pipeline_estadisticas)
```
* **Resultado Obtenido / Esperado:**
```text
• Estado: Aprobado
  Muestras: 138 | Promedio: 224.50 ms | Rango: [8 ms - 448 ms]
• Estado: Rechazado
  Muestras: 74  | Promedio: 231.10 ms | Rango: [12 ms - 450 ms]
• Estado: Pendiente_Revision
  Muestras: 38  | Promedio: 219.80 ms | Rango: [5 ms - 435 ms]
```

---

### Requerimiento 8: Consulta de Complejidad Libre del Equipo

#### Consulta 10: Tasa Porcentual de Aprobación por Docente Titular
* **Objetivo de Negocio:** Analizar la efectividad pedagógica del cuerpo docente vinculando los módulos a su cargo con la totalidad de entregas recibidas, calculando dinámicamente el ratio porcentual de éxito mediante operadores de bifurcación condicional (`$cond`).
* **Etapas del Pipeline:** `$lookup` $\to$ `$unwind` $\to$ `$group` $\to$ `$project` (con `$multiply` y `$divide`) $\to$ `$sort`
* **Comando MQL / PyMongo:**
```python
pipeline_docentes = [
    {
        "$lookup": {
            "from": "entregas_practicas",
            "localField": "_id",
            "foreignField": "modulo_id",
            "as": "entregas"
        }
    },
    {"$unwind": "$entregas"},
    {
        "$group": {
            "_id": "$docente_titular.nombre",
            "especialidad": {"$first": "$docente_titular.especialidad"},
            "total_recibidas": {"$sum": 1},
            "aprobadas": {
                "$sum": {
                    "$cond": [{"$eq": ["$entregas.estado", "Aprobado"]}, 1, 0]
                }
            }
        }
    },
    {
        "$project": {
            "_id": 0,
            "docente": "$_id",
            "especialidad": 1,
            "total_recibidas": 1,
            "aprobadas": 1,
            "efectividad_pct": {
                "$round": [
                    {"$multiply": [{"$divide": ["$aprobadas", "$total_recibidas"]}, 100]},
                    2
                ]
            }
        }
    },
    {"$sort": {"total_recibidas": -1}}
]
db.modulos_sql.aggregate(pipeline_docentes)
```
* **Resultado Obtenido / Esperado:**
```text
• Docente: Dra. Laura Martínez (Modelado Relacional y Normalización)
  Recibidas: 104 | Aprobadas: 58 | Efectividad: 55.77%
• Docente: Mgtr. Carlos Ruiz (Analítica de Datos y Consultas Complejas)
  Recibidas: 98  | Aprobadas: 54 | Efectividad: 55.10%
• Docente: Ing. Roberto Gómez (Optimización y Motores InnoDB)
  Recibidas: 48  | Aprobadas: 26 | Efectividad: 54.17%
```

---

## 3. Índices y Análisis de Rendimiento (Requerimiento 5.5)

### 3.1. Justificación de los Índices Seleccionados
De acuerdo con las consultas de mayor impacto operativo y volumétrico, se seleccionaron dos campos críticos para indexar:
1. **`entregas_practicas.estado`:** La cola de entregas crece indefinidamente. Las consultas de filtrado frecuente para la auditoría docente buscan aislar las entregas `Pendiente_Revision` (un subconjunto minoritario del ~15% del total). Un índice simple sobre este campo permite un acceso directo sin recorrer toda la colección.
2. **`modulos_sql.dificultad`:** Utilizado intensivamente por el catálogo de la plataforma para segmentar las rutas de aprendizaje ofrecidas al estudiante.

### 3.2. Script de Creación de Índices
```python
import pymongo

# Creación de índices en las colecciones correspondientes
idx_entregas = db.entregas_practicas.create_index([("estado", pymongo.ASCENDING)])
idx_modulos = db.modulos_sql.create_index([("dificultad", pymongo.ASCENDING)])

print(f"Índice 1 creado: {idx_entregas}")
print(f"Índice 2 creado: {idx_modulos}")
```

### 3.3. Evidencia y Comparativa con `explain("executionStats")`
Se ejecutó la consulta de búsqueda sobre la cola docente (`{"estado": "Pendiente_Revision"}`) antes y después de construir el índice sobre `entregas_practicas`.

```python
# Consulta ejecutada para el benchmarking
db.entregas_practicas.find({"estado": "Pendiente_Revision"}).explain()["executionStats"]
```

#### Cuadro Comparativo de Rendimiento

| Métrica del Motor | Escenario Previo (Sin Índice) | Escenario Posterior (Con Índice) | Interpretación Técnica |
| :--- | :---: | :---: | :--- |
| **Etapa Principal (`stage`)** | **`COLLSCAN`** | **`IXSCAN` $\to$ `FETCH`** | Sin índice, MongoDB debe realizar un escaneo completo de colección. Con índice, consulta primero el árbol B-Tree del índice (`IXSCAN`) y solo recupera los punteros exactos (`FETCH`). |
| **Documentos Examinados (`totalDocsExamined`)** | **250** | **38** | El índice evitó leer los 212 documentos restantes que no coincidían con el criterio de filtrado. |
| **Documentos Devueltos (`nReturned`)** | **38** | **38** | Ambos devuelven exactamente el mismo resultado semántico. |
| **Ratio de Eficiencia ($\frac{\text{Examinados}}{\text{Devueltos}}$)** | **6.57** | **1.00** | **Eficiencia óptima.** Cada documento leído del almacenamiento fue estrictamente un documento útil para la respuesta. |

### 3.4. Evaluación del Trade-off: Beneficio vs. Costo
* **Beneficio en Lectura:** La complejidad temporal de la consulta se redujo de $O(N)$ (donde $N$ es el total de entregas en la colección) a $O(\log N + K)$ (búsqueda sobre el índice balanceado más la recuperación de $K$ coincidencias). En un escenario a escala con $500.000$ entregas, esta distinción representa la diferencia entre una consulta que demora segundos con saturación de disco frente a una respuesta en submilissegundos.
* **Costo de Mantenimiento y Almacenamiento:** Cada índice exige memoria RAM permanente para permanecer en el working set de WiredTiger y una penalización de escritura durante las inserciones masivas en `entregas_practicas`, dado que el motor debe actualizar el árbol B-Tree por cada nuevo intento registrado. Para NexoSQL este costo resulta plenamente justificable dado que la lectura de la cola docente es un requerimiento de alta concurrencia.

---

## 4. Planteo Preliminar del Caso de Consistencia (Requerimiento 5.6)

Como preparación para la siguiente etapa del proyecto integrador, se definió el caso de negocio donde la consistencia de datos resulta crítica:

* **Operación:** **Aprobación Docente de Entrega con Impacto en Historial Académico.**
* **Riesgo de Inconsistencia:** Si la aplicación actualiza el estado de la entrega a `Aprobado` en `entregas_practicas` pero experimenta una caída de red o de proceso antes de añadir el `modulo_id` al arreglo `modulos_aprobados` del estudiante en la colección `usuarios`, los datos quedan en estado corrupto: el alumno tendrá constancia de su ejercicio aprobado pero la plataforma le bloqueará los módulos correlativos por falta de actualización en su perfil.
* **Estrategia Elegida:** **Transacción Multidocumento.** Dado que la operación compromete dos documentos en colecciones independientes (`entregas_practicas` y `usuarios`), la lógica se implementará utilizando una sesión con transacción de MongoDB (`session.start_transaction()`) para asegurar semántica ACID (todo o nada).

---

## 5. Entregables y Verificación

* **Cuaderno de Consultas:** El archivo `notebooks/consultas.ipynb` contiene las celdas secuenciales de código comentadas junto con sus salidas impresas verificables.
* **Persistencia:** La base de datos opera localmente sobre el puerto configurado en Docker Compose, enlazada a la carpeta de volumen `mongo_data`.