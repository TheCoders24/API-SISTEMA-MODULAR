# 📄 Documentación de Comandos Básicos para Proyecto FastAPI

## 🔹 Activar el entorno virtual

```powershell
.venv\Scripts\Activate.ps1
```

Este comando activa el entorno virtual del proyecto en PowerShell. Al ejecutarlo correctamente, el prompt mostrará el nombre del entorno virtual al inicio, indicando que está activo.

## 🔹 Iniciar el servidor de desarrollo

```powershell
fastapi dev main.py
```

Este comando intenta ejecutar la aplicación `main.py` en modo desarrollo utilizando FastAPI.  
> ⚠️ Asegúrate de tener instalado el paquete que proporciona el comando `fastapi`.

## 🔹 Desactivar el entorno virtual

```powershell
deactivate
```

Este comando desactiva el entorno virtual activo, volviendo al entorno global del sistema.