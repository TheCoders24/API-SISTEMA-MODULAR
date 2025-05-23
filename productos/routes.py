from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.session import get_db
from . import schemas, services

router = APIRouter(prefix="/productos", tags=["productos"])

@router.post("/", response_model=schemas.Producto)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return services.crear_producto(db, producto)

@router.get("/{producto_id}", response_model=schemas.Producto)
def leer_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = services.obtener_producto(db, producto_id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@router.put("/{producto_id}/stock", response_model=schemas.Producto)
def actualizar_stock(producto_id: int, stock: int, db: Session = Depends(get_db)):
    return services.actualizar_stock(db, producto_id, stock)