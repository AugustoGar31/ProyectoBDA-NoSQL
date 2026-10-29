from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from src.repository import ModuloRepository

app = FastAPI(
    title="NexoSQL API",
    description="API REST y Repositorio para la gestión académica de módulos y prácticas SQL en MongoDB",
    version="1.0.0"
)

repo = ModuloRepository()

# --- MODELOS DE VALIDACIÓN (Pydantic) ---

class DocenteSchema(BaseModel):
    nombre: str
    email: str
    especialidad: str

class EjercicioSchema(BaseModel):
    ejercicio_id: int
    consigna: str
    solucion_esperada: str
    puntaje: int = Field(ge=1, le=100)

class ModuloCreateSchema(BaseModel):
    titulo: str
    dificultad: str = Field(description="Baja, Media, Alta o Experto")
    cantidad_inscriptos: int = 0
    docente_titular: DocenteSchema
    ejercicios: List[EjercicioSchema] = []
    video_clase_url: Optional[str] = None
    activo: bool = True

class ModuloUpdateSchema(BaseModel):
    titulo: Optional[str] = None
    dificultad: Optional[str] = None
    cantidad_inscriptos: Optional[int] = None
    video_clase_url: Optional[str] = None
    activo: Optional[bool] = None

# --- ENDPOINTS CRUD (Requerimiento 5.4) ---

@app.post("/modulos", status_code=status.HTTP_201_CREATED, summary="Crear un módulo")
def crear_modulo(modulo: ModuloCreateSchema):
    """Crea un nuevo módulo SQL con sus ejercicios y docente embebidos."""
    creado = repo.create(modulo.model_dump())
    return {"mensaje": "Módulo creado exitosamente", "data": creado}

@app.get("/modulos", summary="Listar módulos con filtros")
def listar_modulos(
    dificultad: Optional[str] = Query(None, description="Filtrar por: Baja, Media, Alta, Experto"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo")
):
    """Retorna la lista de módulos aplicando filtros opcionales."""
    return repo.list_all(dificultad=dificultad, activo=activo)

@app.get("/modulos/{modulo_id}", summary="Obtener un módulo por ID")
def obtener_modulo(modulo_id: str):
    """Recupera el detalle completo de un módulo. Devuelve 404 si no existe."""
    doc = repo.get_by_id(modulo_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"El módulo con ID '{modulo_id}' no fue encontrado o el ID no es válido."
        )
    return doc

@app.put("/modulos/{modulo_id}", summary="Actualizar un módulo")
def actualizar_modulo(modulo_id: str, cambios: ModuloUpdateSchema):
    """Actualiza parcialmente los datos de un módulo. Devuelve 404 si no existe."""
    actualizado = repo.update(modulo_id, cambios.model_dump())
    if not actualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se pudo actualizar: el módulo '{modulo_id}' no existe."
        )
    return {"mensaje": "Módulo actualizado", "data": actualizado}

@app.delete("/modulos/{modulo_id}", status_code=status.HTTP_200_OK, summary="Eliminar un módulo")
def eliminar_modulo(modulo_id: str):
    """Elimina físicamente un módulo de la base de datos."""
    borrado = repo.delete(modulo_id)
    if not borrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se pudo eliminar: el módulo '{modulo_id}' no existe."
        )
    return {"mensaje": f"Módulo '{modulo_id}' eliminado con éxito"}

# --- ENDPOINT CASO DE CONSISTENCIA (Requerimiento 5.6) ---

@app.post("/modulos/{modulo_id}/inscribir", summary="Inscribir estudiante (Operación atómica)")
def inscribir_estudiante(modulo_id: str, usuario_id: str):
    """
    Registra la inscripción de un estudiante e incrementa de forma atómica
    el contador de inscriptos del módulo evitando pérdidas por concurrencia.
    """
    resultado = repo.inscribir_estudiante_atomico(modulo_id, usuario_id)
    if not resultado["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resultado["error"])
    return resultado

# uvicorn src.main:app --reload
# http://127.0.0.1:8000/docs
# python -c "from pymongo import MongoClient; c=MongoClient('mongodb://augusto:password123@localhost:27018/?authSource=admin'); print(c.nexosql_db.usuarios.find_one()['_id'])"
# docker compose logs -f api