import os
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId
from bson.errors import InvalidId
from typing import Optional, List, Dict, Any

class ModuloRepository:
    def __init__(self, uri: Optional[str] = None):
        # Toma la URI de Docker si existe, o usa localhost:27018 por defecto para pruebas locales
        default_uri = "mongodb://augusto:password123@localhost:27018/?authSource=admin"
        self.uri = uri or os.getenv("MONGO_URI", default_uri)
        self.client = MongoClient(self.uri)
        self.db = self.client["nexosql_db"]
        self.collection = self.db["modulos_sql"]
        self.usuarios = self.db["usuarios"]
        self.entregas = self.db["entregas_practicas"]

    def _format_doc(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte ObjectId a string para serialización JSON limpia."""
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    # --- OPERACIONES CRUD (Entidad Principal: modulos_sql) ---

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /modulos - Inserta un nuevo módulo."""
        result = self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._format_doc(data)

    def get_by_id(self, modulo_id: str) -> Optional[Dict[str, Any]]:
        """GET /modulos/:id - Obtiene un módulo por su ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(modulo_id)})
            return self._format_doc(doc)
        except InvalidId:
            return None

    def list_all(self, dificultad: Optional[str] = None, activo: Optional[bool] = None) -> List[Dict[str, Any]]:
        """GET /modulos - Lista módulos con filtros opcionales."""
        filtro = {}
        if dificultad:
            filtro["dificultad"] = dificultad
        if activo is not None:
            filtro["activo"] = activo
            
        docs = self.collection.find(filtro)
        return [self._format_doc(doc) for doc in docs]

    def update(self, modulo_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """PUT/PATCH /modulos/:id - Actualiza atributos de un módulo existente."""
        try:
            # Eliminamos campos nulos para actualizar solo lo enviado
            cleaned_data = {k: v for k, v in update_data.items() if v is not None}
            doc = self.collection.find_one_and_update(
                {"_id": ObjectId(modulo_id)},
                {"$set": cleaned_data},
                return_document=ReturnDocument.AFTER
            )
            return self._format_doc(doc)
        except InvalidId:
            return None

    def delete(self, modulo_id: str) -> bool:
        """DELETE /modulos/:id - Elimina un módulo."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(modulo_id)})
            return result.deleted_count > 0
        except InvalidId:
            return False

    # --- CASO DE CONSISTENCIA Y ATOMICIDAD (Sección 5.6) ---

    def inscribir_estudiante_atomico(self, modulo_id: str, usuario_id: str) -> Dict[str, Any]:
        """
        Operación atómica sobre un documento: incrementa 'cantidad_inscriptos'
        usando el operador $inc nativo de MongoDB para evitar condiciones de carrera.
        """
        try:
            # 1. Validar existencia del estudiante
            usuario = self.usuarios.find_one({"_id": ObjectId(usuario_id)})
            if not usuario:
                return {"success": False, "error": "Estudiante no encontrado"}

            # 2. Incremento atómico en el módulo
            modulo_actualizado = self.collection.find_one_and_update(
                {"_id": ObjectId(modulo_id), "activo": True},
                {"$inc": {"cantidad_inscriptos": 1}},
                return_document=ReturnDocument.AFTER
            )

            if not modulo_actualizado:
                return {"success": False, "error": "Módulo inexistente o inactivo"}

            return {
                "success": True,
                "mensaje": "Inscripción registrada con éxito",
                "modulo_id": str(modulo_actualizado["_id"]),
                "inscriptos_actuales": modulo_actualizado["cantidad_inscriptos"]
            }
        except InvalidId:
            return {"success": False, "error": "Formato de ID inválido"}