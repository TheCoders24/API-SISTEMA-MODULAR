# reportes/presentation/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import Response, StreamingResponse
from typing import List, Optional
import asyncio
from . import schemas
from .dependencias import(get_crear_reporte_caso_uso, get_obtener_reportes_caso_uso, get_generar_reporte_caso_uso, get_exportar_reporte_caso_uso, get_estadisticas_caso_uso )

router = APIRouter(prefix="/reportes", tags=["reportes"])

@router.post("/", response_model=schemas.ReporteResponseSchema, status_code=status.HTTP_201_CREATED)
async def crear_reporte(
    reporte_data: schemas.ReporteCreateSchema,
    crear_caso_uso: get_crear_reporte_caso_uso = Depends(get_crear_reporte_caso_uso),
    usuario_id: str = "usuario_ejemplo"  # En producción obtendrías del token JWT
):
    """Crear un nuevo reporte"""
    try:
        # Convertir schema a DTO
        #from ...application.casos_uso import ReporteCreateDTO
        from ..application.casos_uso import ReporteCreateDTO

        dto = ReporteCreateDTO(
            nombre=reporte_data.nombre,
            tipo=reporte_data.tipo,
            descripcion=reporte_data.descripcion,
            filtros=reporte_data.filtros.dict() if reporte_data.filtros else None,
            formato_salida=reporte_data.formato_salida
        )
        
        # Ejecutar caso de uso
        reporte = await crear_caso_uso.ejecutar(dto, usuario_id)
        
        # Iniciar generación en background
        background_tasks = BackgroundTasks()
        background_tasks.add_task(generar_reporte_background, reporte.id)
        
        return schemas.ReporteResponseSchema(**reporte.to_dict())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creando reporte: {str(e)}"
        )

async def generar_reporte_background(reporte_id: str):
    """Tarea en background para generar reporte"""
    #from .dependencies import get_generar_reporte_caso_uso
    from .dependencias import get_crear_reporte_casos_uso
    from fastapi import Depends
    
    # Aquí necesitarías inyectar las dependencias de otra manera
    # Por simplicidad, creamos nuevas instancias
    #from ..infrastructure.repositories import ReporteRepositoryMemoria
    #from ...infrastructure.services import GeneradorDatosMockService, ExportadorReporteService
    
    from ..infraestructure.repositories import ReporteRepositoryMemoria
    from ..infraestructure.services import GeneradorDatosMockService, ExportadorReporteService

    repo = ReporteRepositoryMemoria()
    generador = GeneradorDatosMockService()
    exportador = ExportadorReporteService()
    
    caso_uso = get_generar_reporte_caso_uso(repo, generador, exportador)
    
    try:
        await caso_uso.ejecutar(reporte_id)
    except Exception as e:
        print(f"Error en generación background: {str(e)}")

@router.get("/", response_model=schemas.ReporteListResponseSchema)
async def listar_reportes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    tipo: Optional[schemas.TipoReporte] = None,
    estado: Optional[schemas.EstadoReporte] = None,
    usuario_id: Optional[str] = None,
    caso_uso: get_obtener_reportes_caso_uso = Depends(get_obtener_reportes_caso_uso)
):
    """Obtener lista de reportes"""
    try:
        reportes = await caso_uso.ejecutar(skip, limit, tipo, estado, usuario_id)
        
        # Obtener total para paginación
        repo = caso_uso.reporte_repo
        todos_reportes = await repo.obtener_todos(tipo=tipo, estado=estado, usuario_id=usuario_id)
        total = len(todos_reportes)
        
        return {
            "reportes": [schemas.ReporteResponseSchema(**r.to_dict()) for r in reportes],
            "total": total,
            "pagina": skip // limit + 1,
            "por_pagina": limit,
            "total_paginas": (total + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo reportes: {str(e)}"
        )

@router.get("/{reporte_id}", response_model=schemas.ReporteResponseSchema)
async def obtener_reporte(
    reporte_id: str,
    caso_uso: get_obtener_reportes_caso_uso = Depends(get_obtener_reportes_caso_uso)
):
    """Obtener un reporte específico"""
    try:
        reportes = await caso_uso.ejecutar(usuario_id=None)  # Obtener todos
        reporte = next((r for r in reportes if r.id == reporte_id), None)
        
        if not reporte:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reporte {reporte_id} no encontrado"
            )
        
        return schemas.ReporteResponseSchema(**reporte.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo reporte: {str(e)}"
        )

@router.post("/{reporte_id}/generar", response_model=schemas.ReporteResponseSchema)
async def generar_reporte(
    reporte_id: str,
    caso_uso: get_generar_reporte_caso_uso = Depends(get_generar_reporte_caso_uso)
):
    """Generar/regenerar un reporte"""
    try:
        reporte = await caso_uso.ejecutar(reporte_id)
        return schemas.ReporteResponseSchema(**reporte.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generando reporte: {str(e)}"
        )

@router.post("/{reporte_id}/exportar")
async def exportar_reporte(
    reporte_id: str,
    export_request: schemas.ExportacionRequestSchema,
    caso_uso: get_generar_reporte_caso_uso = Depends(get_exportar_reporte_caso_uso)
):
    """Exportar reporte en formato específico"""
    try:
        resultado = await caso_uso.ejecutar(reporte_id, export_request.formato)
        reporte = resultado["reporte"]
        
        # Simular contenido del archivo
        contenido = f"Reporte: {reporte.nombre}\nFormato: {export_request.formato.value}".encode('utf-8')
        
        return Response(
            content=contenido,
            media_type=resultado["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={resultado['nombre_archivo']}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error exportando reporte: {str(e)}"
        )

@router.get("/{reporte_id}/descargar")
async def descargar_reporte(
    reporte_id: str,
    caso_uso: get_exportar_reporte_caso_uso = Depends(get_exportar_reporte_caso_uso)
):
    """Descargar reporte generado"""
    try:
        resultado = await caso_uso.ejecutar(reporte_id, "pdf")  # Por defecto PDF
        
        # Simular contenido del archivo
        contenido = f"Contenido del reporte {reporte_id}".encode('utf-8')
        
        return Response(
            content=contenido,
            media_type=resultado["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={resultado['nombre_archivo']}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error descargando reporte: {str(e)}"
        )

@router.get("/estadisticas/resumen", response_model=schemas.EstadisticasResponseSchema)
async def obtener_estadisticas(
    caso_uso: get_obtener_reportes_caso_uso = Depends(get_estadisticas_caso_uso)
):
    """Obtener estadísticas de reportes"""
    try:
        estadisticas = await caso_uso.ejecutar()
        return estadisticas
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.delete("/{reporte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_reporte(
    reporte_id: str,
    repo = Depends(get_crear_reporte_caso_uso)
):
    """Eliminar un reporte"""
    try:
        eliminado = await repo.eliminar(reporte_id)
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reporte {reporte_id} no encontrado"
            )
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error eliminando reporte: {str(e)}"
        )