"""
Esquemas de validación para MongoDB (opcional pero recomendado)
MongoDB no requiere esquema, pero puedes validar documentos
"""

LOG_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["trace_id", "level", "category", "action", "message", "timestamp"],
        "properties": {
            "trace_id": {
                "bsonType": "string",
                "description": "debe ser un string y es requerido"
            },
            "level": {
                "bsonType": "string",
                "enum": ["debug", "info", "warning", "error", "critical"],
                "description": "debe ser un nivel válido"
            },
            "category": {
                "bsonType": "string",
                "enum": ["auth", "authorization", "inventory", "sales", "security", "system", "database", "api"],
                "description": "debe ser una categoría válida"
            },
            "action": {
                "bsonType": "string",
                "description": "debe ser un string y es requerido"
            },
            "message": {
                "bsonType": "string",
                "description": "debe ser un string y es requerido"
            },
            "user_id": {
                "bsonType": ["string", "null"]
            },
            "ip": {
                "bsonType": ["string", "null"]
            },
            "timestamp": {
                "bsonType": "date",
                "description": "debe ser una fecha y es requerido"
            },
            "metadata": {
                "bsonType": ["object", "null"]
            }
        }
    }
}


def setup_validation(db, collection_name: str = "observability_logs"):
    """Configura validación de esquema en MongoDB"""
    command = {
        "collMod": collection_name,
        "validator": LOG_VALIDATOR,
        "validationLevel": "strict",
        "validationAction": "error"
    }
    
    try:
        db.command(command)
    except Exception as e:
        print(f"Nota: {e}")
        print("La colección se creará con validación al primer insert")