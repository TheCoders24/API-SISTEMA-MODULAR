# 📄 Documentación de Comandos Básicos para Proyecto FastAPI

### Solution 1: Recreate the virtual environment
1. Delete the existing virtual environment:
   ```bash
   rm -r .venv
   ```
   (Or manually delete the `.venv` folder in your project directory)

2. Create a new virtual environment:
   ```bash
   python -m venv .venv
   ```


4. Then install FastAPI:
   ```bash
   pip install fastapi
   ```

### Solution 2: Use python -m pip directly
If you don't want to recreate the virtual environment, try:
```bash
python -m pip install fastapi
```


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