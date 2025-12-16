# reportes/presentation/dependencies.py
from typing import Generator
from fastapi import Depends, HTTPException, status
from ..infraestructure.repositories import ReporteRepositoryMemoria
from ..infraestructure.services import GeneradorDatosMockService, ExportadorReporteService
from ..application.casos_uso import (CrearReporteCasoUso,ObtenerEstadisticasCasoUso,GenerarReporteCasoUso,ExportarReporteCasoUso)

# Dependencias para repositorios
def get_reporte_repository():
    return ReporteRepositoryMemoria()

def get_generador_datos():
    return GeneradorDatosMockService()

def get_exportador():
    return ExportadorReporteService()

# Dependencias para casos de uso - TODOS EN SINGULAR
def get_crear_reporte_caso_uso(
    repo = Depends(get_reporte_repository)
):
    return CrearReporteCasoUso(repo)

def get_obtener_reportes_caso_uso(  # SINGULAR: get_obtener_reportes_caso_uso
    repo = Depends(get_reporte_repository)
):
    return get_obtener_reportes_caso_uso(repo)

def get_generar_reporte_caso_uso(
    repo = Depends(get_reporte_repository),
    generador = Depends(get_generador_datos),
    exportador = Depends(get_exportador)
):
    return GenerarReporteCasoUso(repo, generador, exportador)

def get_exportar_reporte_caso_uso(
    repo = Depends(get_reporte_repository)
):
    return ExportarReporteCasoUso(repo)

def get_estadisticas_caso_uso(
    repo = Depends(get_reporte_repository)
):
    return ObtenerEstadisticasCasoUso(repo)