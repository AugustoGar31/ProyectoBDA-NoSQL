# TRABAJO PRÁCTICO INTEGRADOR — BASE DE DATOS APLICADA

## Entrega Parcial 3: API REST, Capa de Repositorios y Caso de Consistencia

### Metadatos del Proyecto

* **Proyecto:** NexoSQL — Plataforma Académica Interactiva para el Aprendizaje y Auditoría de SQL
* **Base de Datos:** `nexosql_db`
* **Entorno de Ejecución:** MongoDB 7.x (Docker Compose), Python 3.x, FastAPI, Uvicorn, Pydantic, PyMongo
* **Entidad Principal Administrada:** `modulos_sql`
* **Colecciones Relacionadas:** `usuarios`, `entregas_practicas`

---

## 1. Arquitectura y Separación de Responsabilidades

Para dar cumplimiento al requerimiento **5.4** de la cátedra, el backend de NexoSQL fue diseñado bajo un patrón arquitectónico en capas que separa de forma estricta la recepción de solicitudes HTTP, la validación de esquemas y el acceso a la base de datos documental.

```
┌─────────────────────────────────────────────────────────────┐
│                 Cliente / Swagger UI / Web                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ Solicitudes HTTP (JSON)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Capa de Presentación y API                    │
│                        (main.py)                            │
│  - Enrutamiento REST (@app.get, @app.post, etc.)            │
│  - Validación de tipos y restricciones (Pydantic)          │
│  - Transformación y control de códigos de estado HTTP       │
└──────────────────────────────┬──────────────────────────────┘
                               │ Métodos de Dominio (Diccionarios / Tipos nativos)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Capa de Repositorio                         │
│                    (repository.py)                          │
│  - Aislamiento de la lógica de PyMongo                      │
│  - Sanitización y conversión de BSON ObjectId a String       │
│  - Operaciones CRUD sobre modulos_sql                        │
│  - Operación atómica de negocio ($inc en MongoDB)           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Conexión TCP / Driver nativo
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Base de Datos MongoDB                      │
│            nexosql_db (Contenedor Docker)                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.1. Capa de API y Validación (`main.py`)
Implementada con **FastAPI**. Se encarga de definir los contratos de comunicación, recibir las solicitudes entrantes, ejecutar la validación declarativa de datos mediante modelos de **Pydantic** y traducir los resultados o excepciones del repositorio a respuestas HTTP normalizadas (`200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`).

### 1.2. Capa de Repositorios (`repository.py`)
Implementada en la clase `ModuloRepository`. Centraliza de manera exclusiva las interacciones con el cliente `MongoClient`. Ningún controlador de la API ejecuta consultas o mutaciones MQL directas. Además, encapsula la conversión del identificador interno inmutable `_id` (de tipo `bson.ObjectId`) a cadenas de texto planas (`id: str`) para evitar fallos de serialización JSON en la capa externa.

---

## 2. Especificación de Endpoints y Operaciones CRUD (Requerimiento 5.4)

La entidad principal `modulos_sql` es administrada a través de un conjunto completo de operaciones CRUD:

| Método HTTP | Endpoint | Código Éxito | Códigos Error | Descripción Funcional |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/modulos` | `201 Created` | `422 Unprocessable` | Da de alta un nuevo módulo didáctico con su docente titular y ejercicios embebidos. |
| **GET** | `/modulos` | `200 OK` | — | Lista los módulos persistidos, permitiendo filtrado opcional por `dificultad` y estado `activo`. |
| **GET** | `/modulos/{modulo_id}` | `200 OK` | `404 Not Found` | Recupera el detalle completo de un curso específico a partir de su ID hexadecimal. |
| **PUT** | `/modulos/{modulo_id}` | `200 OK` | `404 Not Found`, `422` | Actualiza de forma parcial o total los atributos de un módulo existente. |
| **DELETE** | `/modulos/{modulo_id}` | `200 OK` | `404 Not Found` | Realiza la eliminación física de un módulo en la base de datos. |
| **POST** | `/modulos/{modulo_id}/inscribir` | `200 OK` | `400 Bad Request`, `404` | Registra la inscripción de un estudiante aplicando consistencia atómica sobre el contador. |

---

## 3. Esquemas de Datos y Validación (Pydantic)

Se implementaron esquemas fuertemente tipados para blindar la entrada de datos a la base documental, impidiendo la inserción de documentos incompletos o inconsistentes:

* **`DocenteSchema`:** Valida que el documento embebido del profesor contenga `nombre`, `email` institucional y `especialidad`.
* **`EjercicioSchema`:** Asegura que cada consigna embebida cuente con `ejercicio_id`, texto de `consigna`, `solucion_esperada` en SQL y un `puntaje` restringido estrictamente entre 1 y 100 puntos mediante validadores de rango:
  $$\text{puntaje} \in [1, 100]$$
* **`ModuloCreateSchema`:** Exige los campos obligatorios del curso, admite opcionalmente la URL multimedia (`video_clase_url`) y valida que la dificultad declarada responda a los niveles pedagógicos del sistema (`Baja`, `Media`, `Alta`, `Experto`).
* **`ModuloUpdateSchema`:** Declara todos los atributos como opcionales (`Optional[...] = None`) para habilitar actualizaciones flexibles sin forzar el reenvío del documento completo.

---

## 4. Implementación y Justificación del Caso de Consistencia (Requerimiento 5.6)

El requerimiento **5.6** estipula identificar una operación de negocio crítica, explicar los riesgos ante fallos o concurrencia y fundamentar la solución técnica adoptada.

### 4.1. Descripción de la Operación de Negocio
**Inscripción de un Estudiante a un Módulo y Actualización de Vacantes.**  
Cuando un estudiante decide cursar una unidad temática, el sistema debe asegurar que el usuario existe en el padrón institucional (`usuarios`) y registrar el incremento correlativo en el atributo `cantidad_inscriptos` de la colección `modulos_sql`.

### 4.2. Análisis del Problema ante Fallos y Concurrencia (Lost Update)
Si esta operación se implementara mediante un flujo clásico de aplicación en dos pasos:
1. `doc = collection.find_one({"_id": modulo_id})` (Lectura del contador actual, ej: 40)
2. `collection.update_one({"_id": modulo_id}, {"$set": {"cantidad_inscriptos": doc["cantidad_inscriptos"] + 1}})`

En un entorno con concurrencia real donde dos estudiantes ($E_1$ y $E_2$) solicitan la inscripción en la misma fracción de segundo, ambos procesos leerían el valor $40$. Ambos calcularían $40 + 1 = 41$ y ambos escribirían $41$. Como resultado, se perdería una inscripción (**Condición de Carrera / Pérdida de Actualización**), violando la consistencia del estado de vacantes de la plataforma.

### 4.3. Solución Implementada: Operación Atómica en un Documento
Para resolver este escenario sin incurrir en la penalización de rendimiento de transacciones pesadas, se implementó una **operación atómica nativa a nivel de documento único** en el repositorio utilizando `find_one_and_update` junto con el operador `$inc` de MongoDB:

```python
modulo_actualizado = self.collection.find_one_and_update(
    {"_id": ObjectId(modulo_id), "activo": True},
    {"$inc": {"cantidad_inscriptos": 1}},
    return_document=ReturnDocument.AFTER
)
```

#### Justificación Técnica de la Elección:
1. **Garantía de Atomicidad en el Motor:** MongoDB garantiza que las modificaciones sobre un único documento son intrínsecamente atómicas. El operador `$inc` realiza la suma directamente en el espacio de memoria del motor sin requerir el ciclo de lectura-modificación-escritura en la aplicación, neutralizando cualquier condición de carrera.
2. **Simplicidad y Eficiencia Operativa:** Al residir el contador dentro de la propia entidad `modulos_sql`, no se justifica la sobrecarga computacional de abrir una sesión transaccional distribuida (`session.start_transaction()`).
3. **Validación Previa de Integridad:** Antes de disparar el incremento atómico, el repositorio verifica la existencia previa del `usuario_id` en la colección `usuarios`. Si el estudiante no existe, la operación aborta inmediatamente devolviendo un código `400 Bad Request`, asegurando que no se incrementen contadores por solicitudes huérfanas o erróneas.

---

## 5. Pruebas y Evidencia de Ejecución (Swagger UI)

La API expone su documentación interactiva OpenAPI en `http://127.0.0.1:8000/docs`, mediante la cual se comprobaron los siguientes escenarios:

### 5.1. Prueba 1: Creación Exitosa de un Módulo (`POST /modulos`)
* **Entrada (Request Body):**
  ```json
  {
    "titulo": "Optimización y Planes de Ejecución",
    "dificultad": "Experto",
    "cantidad_inscriptos": 0,
    "docente_titular": {
      "nombre": "Ing. Roberto Gómez",
      "email": "rgomez@nexosql.edu",
      "especialidad": "Optimización y Motores InnoDB"
    },
    "ejercicios": [
      {
        "ejercicio_id": 1,
        "consigna": "Analizar costo computacional usando EXPLAIN ANALYZE.",
        "solucion_esperada": "EXPLAIN ANALYZE SELECT * FROM facturas;",
        "puntaje": 100
      }
    ],
    "video_clase_url": "https://nexosql.edu/clases/explain-analyze",
    "activo": true
  }
  ```
* **Respuesta del Servidor:** Código **`201 Created`**. Retorna el objeto creado con su identificador generado por MongoDB (ej: `"id": "6ae2717fcae08605ff2f9764"`).

### 5.2. Prueba 2: Búsqueda por Identificador Válido (`GET /modulos/{id}`)
* **Parámetro:** `modulo_id = "6ae2717fcae08605ff2f9764"`
* **Respuesta del Servidor:** Código **`200 OK`**. Retorna la estructura completa del documento con sus ejercicios embebidos intactos.

### 5.3. Prueba 3: Manejo de Identificador Inexistente o Inválido (`GET /modulos/{id}`)
* **Parámetro:** `modulo_id = "201"` (o cualquier cadena que no cumpla con el formato BSON de 24 caracteres hexadecimales).
* **Respuesta del Servidor:** Código **`404 Not Found`**.
  ```json
  {
    "detail": "El módulo con ID '201' no fue encontrado o el ID no es válido."
  }
  ```

### 5.4. Prueba 4: Caso de Consistencia con Éxito (`POST /modulos/{id}/inscribir`)
* **Parámetros:** `modulo_id = "6ae2717fcae08605ff2f9764"`, `usuario_id = "67201b1a9a1b8c2d3e4f0105"` (estudiante real existente en la base).
* **Respuesta del Servidor:** Código **`200 OK`**.
  ```json
  {
    "success": true,
    "mensaje": "Inscripción registrada con éxito",
    "modulo_id": "6ae2717fcae08605ff2f9764",
    "inscriptos_actuales": 1
  }
  ```

### 5.5. Prueba 5: Caso de Consistencia con Falla Controlada (`POST /modulos/{id}/inscribir`)
* **Parámetros:** `modulo_id = "6ae2717fcae08605ff2f9764"`, `usuario_id = "000000000000000000000000"` (estudiante ficticio inexistente).
* **Respuesta del Servidor:** Código **`400 Bad Request`**.
  ```json
  {
    "detail": "Estudiante no encontrado"
  }
  ```
  *Verificación:* El contador `cantidad_inscriptos` se mantuvo inalterado, demostrando la integridad de los datos ante peticiones fallidas.

---

## 6. Instrucciones para la Ejecución Local

Para levantar el entorno y verificar la solución en una máquina limpia:

1. **Asegurar la base de datos operativa:**
   ```powershell
   docker compose up -d
   ```
2. **Activar el entorno virtual:**
   ```powershell
   .\venv\Scripts\activate
   ```
3. **Instalar dependencias de la API (si no estuvieran instaladas):**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Iniciar el servidor Uvicorn con recarga en caliente:**
   ```powershell
   uvicorn src.main:app --reload
   ```
5. **Acceder a la suite interactiva de pruebas:**
   Ingresar desde cualquier navegador a `http://127.0.0.1:8000/docs`.