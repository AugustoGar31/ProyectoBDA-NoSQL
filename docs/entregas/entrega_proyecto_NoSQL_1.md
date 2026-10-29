# TRABAJO PRÁCTICO INTEGRADOR — BASE DE DATOS APLICADA
## Entrega Parcial 1: Propuesta, Análisis y Diseño de Base de Datos Documental

---

### Metadatos del Proyecto
* **Proyecto:** NexoSQL — Plataforma Académica Interactiva para el Aprendizaje y Auditoría de SQL
* **Dominio Seleccionado:** Plataforma Académica
* **Motor de Base de Datos:** MongoDB Community Edition (Dockerizado)
* **Entorno de Ejecución:** Docker Compose, Python (PyMongo, Faker), Jupyter Notebook

---

## 1. Descripción de la Problemática y Justificación del Dominio

### 1.1. Contexto y Problema
En la formación técnica universitaria sobre bases de datos, la adquisición de habilidades prácticas en la escritura de consultas estructuradas (SQL) suele verse obstaculizada por la falta de retroalimentación inmediata sobre la calidad, corrección semántica y rendimiento de las sentencias ejecutadas. Las herramientas tradicionales de gestión educativa (LMS genéricos) se limitan a recibir entregas en archivos de texto o formularios estáticos, desvinculando la entrega práctica del análisis de performance en el motor de base de datos y de la supervisión docente personalizada.

**NexoSQL** nace como una plataforma académica interactiva enfocada en el aprendizaje práctico guiado. Permite a los estudiantes interactuar con módulos temáticos y consignas de código, ejecutar consultas y registrar sus intentos, al tiempo que dota a los docentes de herramientas analíticas para auditar la eficiencia computacional de las soluciones, detectar trabas conceptuales y proveer devoluciones cualitativas y cuantitativas sobre los ejercicios más complejos.

### 1.2. Justificación del Dominio
El proyecto se encuadra en el dominio de **Plataforma académica**, cubriendo la gestión didáctica de contenidos, seguimiento estudiantil y evaluación práctica. Se opta por una arquitectura basada en **3 colecciones** interconectadas (`modulos_sql`, `usuarios`, `entregas_practicas`), lo que excede el piso mínimo exigido de dos colecciones, garantizando un ecosistema de datos representativo para operaciones de agregación complejas, indexación estratégica y control transaccional de consistencia.

---

## 2. Actores y Usuarios Involucrados

1. **Estudiante:** 
   * Explora el catálogo de módulos teóricos y prácticos según su nivel de dificultad.
   * Consulta las consignas de ejercicios y ejecuta sus soluciones en SQL.
   * Visualiza el historial de resoluciones aprobadas, rechazadas o pendientes, así como las devoluciones emitidas por los docentes.
2. **Docente Titular:**
   * Diseña y mantiene los módulos de estudio, incorporando consignas y soluciones de referencia.
   * Audita la cola de entregas prácticas en estado pendiente de revisión.
   * Proporciona retroalimentación pedagógica y calificación manual en entregas atípicas o de nivel avanzado.
3. **Sistema Automatizado / Administrador:**
   * Registra automáticamente las métricas de ejecución de cada intento (latencia en milisegundos y cantidad de reintentos).
   * Consolida métricas de uso y tasa de aprobación general por comisión horaria.

---

## 3. Requerimientos Funcionales

* **RF1 - Administración de Módulos (CRUD Principal):** La plataforma debe permitir el alta, consulta detallada, actualización de contenidos y baja lógica/física de módulos de aprendizaje junto con sus desafíos prácticos.
* **RF2 - Gestión de Estudiantes y Progresión:** Registro de usuarios clasificados por comisiones de cursada (`Comisión Mañana`, `Comisión Tarde`, `Comisión Noche`), trazando el conjunto de módulos completados y casos límite de alumnos sin avance.
* **RF3 - Registro de Envíos y Telemetría de Consultas:** Persistencia de cada intento de resolución enviado por los alumnos, almacenando la sentencia SQL remitida, el tiempo de respuesta del motor en milisegundos y el conteo de intentos fallidos.
* **RF4 - Auditoría y Evaluación Docente:** Capacidad de filtrar soluciones críticas que requieran revisión humana, permitiendo al profesor adjuntar comentarios formativos y calificaciones numéricas.
* **RF5 - Análisis y Extracción de Indicadores:** Ejecución de consultas analíticas para medir tiempos medios de procesamiento por estado, tasa de aprobación por profesor a cargo y ranking de desempeño estudiantil.

---

## 4. Justificación Técnica: Modelo Documental vs. Modelo Relacional

Conforme a los criterios de evaluación arquitectónica provistos por la cátedra, la elección de un modelo documental sobre MongoDB en contraposición a una base relacional (MySQL) se fundamenta en las siguientes 5 preguntas de diseño:

### 1. ¿Cuál es la consulta más frecuente?
* **Análisis NexoSQL:** La consulta más recurrente del sistema ocurre cuando un estudiante ingresa a practicar un módulo. En ese instante, la interfaz exige cargar en una única operación: título, nivel de dificultad, información de contacto del docente titular y el listado íntegro de ejercicios con sus consignas y puntajes.
* **Decisión:** En un motor relacional, esta acción demandaría múltiples operaciones `JOIN` entre tablas normalizadas (`modulo`, `docente`, `ejercicio`). En MongoDB, la totalidad de la vista se resuelve mediante **una sola lectura atómica sobre un único documento** gracias al anidamiento de subdocumentos y arreglos de ejercicios.

### 2. ¿Los registros tienen siempre los mismos campos?
* **Análisis NexoSQL:** La información presenta notable heterogeneidad:
  * Ciertos módulos incluyen enlaces a clases grabadas (`video_clase_url`), mientras otros son puramente textuales.
  * Ciertos estudiantes vinculan su perfil público (`github_url`) y otros omiten este dato.
  * En la colección de entregas, el objeto de retroalimentación docente (`revision_docente`) solo existe cuando hubo una corrección manual, careciendo de sentido para entregas evaluadas de forma 100% automática.
* **Decisión:** El esquema flexible de MongoDB evita la proliferación de columnas nulas innecesarias o tablas accesorias de clave-valor propias de los esquemas tabulares rígidos.

### 3. ¿Qué tan importante es la integridad referencial delegada al motor?
* **Análisis NexoSQL:** El modelo no responde a un libro mayor contable ni a un procesamiento de pagos bancarios donde una llave foránea huérfana comprometa legalmente el negocio.
* **Decisión:** La integridad entre estudiantes, módulos y entregas es gestionada eficientemente por la capa de lógica de negocio (Python / FastAPI) y la capa de repositorios al momento de persistir datos, haciendo prescindible el costo de bloqueo y validación por claves foráneas a nivel de motor.

### 4. ¿Se requieren transacciones complejas entre múltiples entidades?
* **Análisis NexoSQL:** La vasta mayoría de las transacciones son locales a una entidad (ej. agregar un ejercicio nuevo a un módulo o actualizar el tiempo de respuesta de una entrega).
* **Decisión:** MongoDB garantiza atomicidad a nivel de documento único sin recurrir a mecanismos pesados de bloqueo. Para el caso puntual de sincronización simultánea (aprobar una entrega y actualizar el perfil del usuario), el motor admite transacciones multidocumento puntuales sobre la misma sesión.

### 5. ¿Cómo es el volumen, la velocidad y la variedad de los datos?
* **Análisis NexoSQL:** La actividad estudiantil genera un flujo de escrituras veloz y continuo debido a las constantes pruebas y correcciones de código SQL ejecutadas en simultáneo por cientos de alumnos.
* **Decisión:** El almacenamiento en formato BSON optimiza las escrituras de alta velocidad y admite escalabilidad horizontal natural frente al crecimiento del volumen de telemetría de las prácticas.

---

## 5. Diseño Estructural de la Base de Datos

### 5.1. Diagrama de Relaciones y Patrones de Modelado

```
┌────────────────────────────────────────────────────────┐
│                      modulos_sql                       │
├────────────────────────────────────────────────────────┤
│ _id: ObjectId                                          │
│ titulo: String                                         │
│ dificultad: String (Baja | Media | Alta | Experto)     │
│ cantidad_inscriptos: Number                            │
│ activo: Boolean                                        │
│ video_clase_url: String? [Opcional]                    │
│ docente_titular: Object [Subdocumento Embebido]        │
│   ├── nombre: String                                   │
│   ├── email: String                                    │
│   └── especialidad: String                             │
│ ejercicios: Array<Object> [Arreglo Embebido]           │
│   ├── ejercicio_id: Number                             │
│   ├── consigna: String                                 │
│   ├── solucion_esperada: String                        │
│   └── puntaje: Number                                  │
└───────────────────────────┬────────────────────────────┘
                            │ (Referenciado en entregas y usuarios)
                            │
         ┌──────────────────┴──────────────────┐
         │                                     │
         ▼                                     ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│       entregas_practicas        │   │            usuarios             │
├─────────────────────────────────┤   ├─────────────────────────────────┤
│ _id: ObjectId                   │   │ _id: ObjectId                   │
│ usuario_id: ObjectId [Ref]──────┼──►│ nombre: String                  │
│ modulo_id: ObjectId [Ref]       │   │ email: String (Único)           │
│ ejercicio_numero: Number        │   │ comision: String                │
│ query_enviada: String           │   │ fecha_registro: ISODate         │
│ estado: String                  │   │ github_url: String? [Opcional]  │
│ tiempo_ejecucion_ms: Number     │   │ modulos_aprobados: Array<Ref>   │
│ intentos: Number                │   │   └── [ ObjectId, ... ]         │
│ fecha_entrega: ISODate          │   └─────────────────────────────────┘
│ revision_docente: Object? [Opc] │
│   ├── comentario: String        │
│   ├── calificacion_manual: Num  │
│   └── fecha_revision: ISODate   │
└─────────────────────────────────┘
```

---

## 6. Especificación de Colecciones y Documentos BSON

### 6.1. Colección Principal: `modulos_sql`
Centraliza el contenido pedagógico.

* **Atributos Obligatorios:**
  * `_id` (`ObjectId`): Identificador único inmutable generado por MongoDB.
  * `titulo` (`String`): Nombre descriptivo de la unidad temática.
  * `dificultad` (`String`): Categorización de complejidad (`Baja`, `Media`, `Alta`, `Experto`).
  * `cantidad_inscriptos` (`Number`): Contador acumulativo de estudiantes cursando el módulo.
  * `activo` (`Boolean`): Bandera para deshabilitación lógica sin pérdida histórica.
  * `docente_titular` (`Object`): Documento anidado con los datos del profesor responsable.
  * `ejercicios` (`Array`): Arreglo de desafíos embebidos que componen la ejercitación práctica.
* **Atributos Opcionales:**
  * `video_clase_url` (`String`): Enlace multimedia complementario cuando el módulo cuenta con grabación sincrónica.

**Ejemplo de Documento BSON (`modulos_sql`):**
```json
{
  "_id": { "$oid": "67201a4f9a1b8c2d3e4f0001" },
  "titulo": "Optimización, Índices y Transacciones",
  "dificultad": "Experto",
  "cantidad_inscriptos": 48,
  "activo": true,
  "video_clase_url": "https://nexosql.edu/clases/optimizacion-avanzada",
  "docente_titular": {
    "nombre": "Ing. Roberto Gómez",
    "email": "rgomez@nexosql.edu",
    "especialidad": "Optimización y Motores InnoDB"
  },
  "ejercicios": [
    {
      "ejercicio_id": 1,
      "consigna": "Crear un índice compuesto para agilizar el filtrado por cliente y fecha de factura.",
      "solucion_esperada": "CREATE INDEX idx_cliente_fecha ON facturas(cliente_id, fecha_emision);",
      "puntaje": 50
    },
    {
      "ejercicio_id": 2,
      "consigna": "Diseñar una transacción atómica para asentar el débito y crédito de una transferencia contable.",
      "solucion_esperada": "START TRANSACTION; UPDATE cuentas SET balance = balance - 100 WHERE id = 1; UPDATE cuentas SET balance = balance + 100 WHERE id = 2; COMMIT;",
      "puntaje": 50
    }
  ]
}
```

---

### 6.2. Colección Secundaria 1: `usuarios`
Registra la identidad y el progreso general del estudiantado.

* **Atributos Obligatorios:**
  * `_id` (`ObjectId`): Identificador único del usuario.
  * `nombre` (`String`): Nombre y apellido del estudiante.
  * `email` (`String`): Dirección institucional única de correo electrónico.
  * `comision` (`String`): Comisión horaria a la que pertenece (`Comisión Mañana`, `Comisión Tarde`, `Comisión Noche`).
  * `fecha_registro` (`ISODate`): Marca temporal de alta en la plataforma.
  * `modulos_aprobados` (`Array<ObjectId>`): Lista de identificadores referenciados correspondientes a módulos que el alumno ha completado satisfactoriamente.
* **Atributos Opcionales:**
  * `github_url` (`String`): Vínculo opcional al perfil de desarrollo del estudiante.
* **Casos Límite:**
  * Alumnos recién dados de alta poseen la lista `modulos_aprobados` con tamaño cero (`[]`), situación modelada para evaluar el comportamiento del sistema ante usuarios sin actividad académica.

**Ejemplo de Documento BSON (`usuarios`):**
```json
{
  "_id": { "$oid": "67201b1a9a1b8c2d3e4f0105" },
  "nombre": "Lucas Almada",
  "email": "lucas.almada@nexosql.edu",
  "comision": "Comisión Noche",
  "fecha_registro": { "$date": "2026-03-15T18:22:10.000Z" },
  "github_url": "https://github.com/lucasalmada-dev",
  "modulos_aprobados": [
    { "$oid": "67201a4f9a1b8c2d3e4f0001" }
  ]
}
```

---

### 6.3. Colección Secundaria 2: `entregas_practicas`
Modela el historial transaccional de código ejecutado y su proceso evaluativo.

* **Atributos Obligatorios:**
  * `_id` (`ObjectId`): Identificador único de la entrega.
  * `usuario_id` (`ObjectId`): Referencia al estudiante emisor de la solución.
  * `modulo_id` (`ObjectId`): Referencia al módulo temático donde radica el ejercicio.
  * `ejercicio_numero` (`Number`): Número ordinal del ejercicio dentro del módulo.
  * `query_enviada` (`String`): Sentencia SQL remitida por el estudiante para validación.
  * `estado` (`String`): Estado actual del intento (`Aprobado`, `Rechazado`, `Pendiente_Revision`).
  * `tiempo_ejecucion_ms` (`Number`): Latencia de cómputo registrada durante la ejecución de la consulta.
  * `intentos` (`Number`): Conteo acumulado de ejecuciones realizadas antes de obtener el estado final.
  * `fecha_entrega` (`ISODate`): Marca de tiempo del envío de la solución.
* **Atributos Opcionales / Anidados:**
  * `revision_docente` (`Object`): Subdocumento anidado que almacena la corrección pedagógica manual (`comentario`, `calificacion_manual` entre 1 y 10, y `fecha_revision`). Presente únicamente en entregas revisadas por un docente.

**Ejemplo de Documento BSON (`entregas_practicas`):**
```json
{
  "_id": { "$oid": "67201c339a1b8c2d3e4f0320" },
  "usuario_id": { "$oid": "67201b1a9a1b8c2d3e4f0105" },
  "modulo_id": { "$oid": "67201a4f9a1b8c2d3e4f0001" },
  "ejercicio_numero": 1,
  "query_enviada": "CREATE INDEX idx_cliente_fecha ON facturas(cliente_id, fecha_emision);",
  "estado": "Aprobado",
  "tiempo_ejecucion_ms": 14,
  "intentos": 2,
  "fecha_entrega": { "$date": "2026-04-10T21:40:00.000Z" },
  "revision_docente": {
    "comentario": "Excelente criterio al definir el índice compuesto respetando la selectividad de los campos.",
    "calificacion_manual": 10,
    "fecha_revision": { "$date": "2026-04-11T09:15:30.000Z" }
  }
}
```

---

## 7. Justificación de Decisiones de Modelado (Embebidos vs. Referencias)

El diseño documental implementado atiende rigurosamente a los patrones de acceso previstos, el volumen proyectado y las restricciones estructurales de BSON:

### 7.1. Decisión de Embeber (Documentos y Arreglos Anidados)
* **Docente titular dentro de `modulos_sql`:** La relación módulo-docente en este alcance es estrictamente de lectura unificada. Al desplegar la ficha de un curso, se requiere conocer quién es el docente responsable de forma inmediata. Como los datos del profesor (`nombre`, `email`, `especialidad`) presentan una tasa de mutación prácticamente nula, embeberlos elimina la penalización de rendimiento que implicaría realizar operaciones de consulta adicionales o `$lookup`.
* **Ejercicios dentro de `modulos_sql`:** La relación es de tipo **1 a Pocos Acotados** (entre 2 y 5 ejercicios por módulo). Un ejercicio carece de ciclo de vida independiente fuera de su módulo temático: nace, se modifica y se visualiza exclusivamente dentro del curso al que pertenece. Embeberlos en un arreglo asegura lectura en una única operación BSON y garantiza atomicidad en las actualizaciones del temario.

### 7.2. Decisión de Referenciar (Identificadores `ObjectId`)
* **Entregas prácticas en colección independiente (`entregas_practicas`):** Constituye una relación de tipo **1 a Muchos Ilimitados**. Cada estudiante produce decenas o cientos de envíos a lo largo de su cursada. Si se embebieran los intentos dentro del documento del estudiante (`usuarios`) o dentro del curso (`modulos_sql`), los documentos crecerían sin control, arriesgando la superación del límite físico de **16 MB por documento BSON** e incrementando innecesariamente el consumo de memoria RAM al recuperar perfiles básicos.
* **Separación para análisis transversal:** Las entregas requieren consultas analíticas directas y desacopladas (medir tiempos de ejecución promedio, calcular dispersión de latencias o filtrar la cola de pendientes de revisión). Al encontrarse en su propia colección, estas consultas se ejecutan con alta eficiencia mediante índices específicos sin necesidad de proyectar estructuras superiores masivas.
* **Módulos aprobados referenciados en `usuarios`:** Se optó por una lista de referencias compactas (`Array<ObjectId>`). Esto mantiene al documento de usuario liviano y desacoplado, permitiendo que cualquier modificación en el título o contenido de un módulo impacte de forma transparente sin requerir actualizaciones en cascada sobre los perfiles estudiantiles.

---

## 8. Infraestructura y Entorno Reproducible

Para garantizar la reproducibilidad estricta de la solución desde la primera etapa del proyecto, el motor de base de datos se encuentra contenerizado bajo las siguientes directivas:

* **Servicio:** MongoDB Community Server 7.x (`mongo:latest`).
* **Orquestación:** Docker Compose exponiendo el puerto de servicio y administrando redes internas aisladas.
* **Persistencia:** Volumen enlazado localmente (`mongo_data`) para asegurar la preservación de los datos ante detenciones del contenedor.
* **Seguridad y Control de Acceso:** Variables de inicialización de credenciales administrativas desacopladas en archivos de entorno (`.env`).