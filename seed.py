from pymongo import MongoClient
from faker import Faker
import random

# Conexión a MongoDB con tus credenciales configuradas
client = MongoClient(
    "mongodb://augusto:password123@localhost:27018/?authSource=admin"
)
db = client["nexosql_db"]

# Limpiar colecciones previas para garantizar reproducibilidad
db.modulos_sql.drop()
db.usuarios.drop()
db.entregas_practicas.drop()

fake = Faker('es_ES')

# --- 1. POBLAR MÓDULOS SQL CON DOCENTES Y EJERCICIOS EMBEBIDOS ---
docentes = [
    {"nombre": "Ing. Roberto Gómez", "email": "rgomez@nexosql.edu", "especialidad": "Optimización y Motores InnoDB"},
    {"nombre": "Dra. Laura Martínez", "email": "lmartinez@nexosql.edu", "especialidad": "Modelado Relacional y Normalización"},
    {"nombre": "Mgtr. Carlos Ruiz", "email": "cruiz@nexosql.edu", "especialidad": "Analítica de Datos y Consultas Complejas"}
]

modulos_data = [
    {"titulo": "Select Básico y Filtrado", "dificultad": "Baja", "docente": docentes[1]},
    {"titulo": "Joins (Inner, Left, Right)", "dificultad": "Media", "docente": docentes[1]},
    {"titulo": "Funciones de Agregación y Group By", "dificultad": "Media", "docente": docentes[2]},
    {"titulo": "Subconsultas y CTEs", "dificultad": "Alta", "docente": docentes[2]},
    {"titulo": "Optimización, Índices y Transacciones", "dificultad": "Experto", "docente": docentes[0]}
]

queries_ejemplo = [
    "SELECT nombre, email FROM clientes WHERE activo = 1;",
    "SELECT c.nombre, COUNT(p.id) FROM clientes c JOIN pedidos p ON c.id = p.cliente_id GROUP BY c.nombre;",
    "SELECT dept_id, AVG(salario) FROM empleados GROUP BY dept_id HAVING AVG(salario) > 5000;",
    "WITH ventas_anuales AS (SELECT vendedor_id, SUM(monto) AS total FROM ventas GROUP BY vendedor_id) SELECT * FROM ventas_anuales WHERE total > 10000;",
    "CREATE INDEX idx_cliente_fecha ON facturas(cliente_id, fecha_emision);"
]

modulos_insertados = []
for mod in modulos_data:
    num_ejercicios = random.randint(2, 4)
    ejercicios = []
    for i in range(num_ejercicios):
        ejercicios.append({
            "ejercicio_id": i + 1,
            "consigna": fake.sentence(nb_words=10),
            "solucion_esperada": random.choice(queries_ejemplo),
            "puntaje": random.choice([10, 20, 50])
        })
    
    documento_modulo = {
        "titulo": mod["titulo"],
        "dificultad": mod["dificultad"],
        "cantidad_inscriptos": random.randint(15, 60),
        "docente_titular": mod["docente"], # Objeto anidado con datos del profesor
        "ejercicios": ejercicios,          # Arreglo de documentos embebidos
        "activo": True
    }
    
    # Atributo opcional: URL de clase grabada por el profesor
    if random.choice([True, False]):
        documento_modulo["video_clase_url"] = f"https://nexosql.edu/clases/{fake.lexify(text='??????')}"
        
    res = db.modulos_sql.insert_one(documento_modulo)
    modulos_insertados.append(res.inserted_id)

print(f"[OK] Se insertaron {len(modulos_insertados)} módulos SQL con sus docentes y ejercicios.")


# --- 2. POBLAR USUARIOS (ESTUDIANTES) ---
usuarios_insertados = []
comisiones = ["Comisión Mañana", "Comisión Tarde", "Comisión Noche"]

for _ in range(120):
    # Caso límite: alumnos con 0 módulos aprobados (recién inscriptos)
    num_aprobados = random.choices([0, 1, 2, 3, 4], weights=[25, 30, 25, 15, 5])[0]
    modulos_aprobados = random.sample(modulos_insertados, num_aprobados)
    
    documento_usuario = {
        "nombre": fake.name(),
        "email": fake.unique.email(),
        "comision": random.choice(comisiones),
        "fecha_registro": fake.date_time_between(start_date="-1y", end_date="now"),
        "modulos_aprobados": modulos_aprobados
    }
    
    # Atributo opcional
    if random.choice([True, False]):
        documento_usuario["github_url"] = f"https://github.com/{fake.user_name()}"
        
    res_user = db.usuarios.insert_one(documento_usuario)
    usuarios_insertados.append(res_user.inserted_id)

print(f"[OK] Se insertaron {len(usuarios_insertados)} estudiantes.")


# --- 3. POBLAR ENTREGAS PRÁCTICAS (CONEXIÓN ALUMNO - VERIFICADOR - PROFESOR) ---
entregas_count = 0
estados_posibles = ["Aprobado", "Rechazado", "Pendiente_Revision"]
comentarios_profe = [
    "Excelente uso de índices compuestos, muy buen tiempo de respuesta.",
    "La consulta devuelve los datos correctos, pero evitá usar SELECT * en producción.",
    "Falta la cláusula GROUP BY para agrupar correctamente las funciones de agregación.",
    "Muy buena resolución aplicando CTEs para mejorar la legibilidad."
]

for _ in range(250):
    estado_actual = random.choices(estados_posibles, weights=[55, 30, 15])[0]
    
    entrega_doc = {
        "usuario_id": random.choice(usuarios_insertados),
        "modulo_id": random.choice(modulos_insertados),
        "ejercicio_numero": random.randint(1, 3),
        "query_enviada": random.choice(queries_ejemplo),
        "estado": estado_actual,
        "tiempo_ejecucion_ms": random.randint(5, 450),
        "intentos": random.randint(1, 6),
        "fecha_entrega": fake.date_time_between(start_date="-6m", end_date="now")
    }
    
    # Si ya fue evaluado (no está pendiente) y el profesor dejó devolución (atributo opcional anidado)
    if estado_actual != "Pendiente_Revision" and random.choice([True, False]):
        entrega_doc["revision_docente"] = {
            "comentario": random.choice(comentarios_profe),
            "calificacion_manual": random.randint(6, 10) if estado_actual == "Aprobado" else random.randint(2, 5),
            "fecha_revision": fake.date_time_between(start_date="-1m", end_date="now")
        }
        
    db.entregas_practicas.insert_one(entrega_doc)
    entregas_count += 1

print(f"[OK] Se insertaron {entregas_count} entregas de ejercicios SQL.")