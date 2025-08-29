# infrastructure/logger/utils.py
import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizar datos sensibles en los logs"""
    if not data:
        return {}
    
    sanitized = data.copy()
    sensitive_fields = [
        'password', 'token', 'authorization', 'secret', 
        'key', 'access_token', 'refresh_token', 'credentials',
        'api_key', 'jwt', 'bearer'
    ]
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '***REDACTED***'
        # También buscar en nested objects
        for key, value in sanitized.items():
            if isinstance(value, dict) and field in value:
                value[field] = '***REDACTED***'
    
    return sanitized

def ensure_logs_dir(logs_dir: str) -> Path:
    """Asegurar que el directorio de logs existe en la ruta seleccionada"""
    log_path = Path(logs_dir)
    log_path.mkdir(exist_ok=True, parents=True)
    return log_path



def get_current_log_file(logs_dir: str) -> Path:
    """Obtener el archivo de log actual basado en la fecha actual"""
    log_path = ensure_logs_dir(logs_dir)
    return log_path / f"api_errors_{datetime.now().strftime('%Y%m%d')}.txt"

def clean_old_logs(logs_dir: str, days_to_keep: int = 30):
    """Limpiar logs más antiguos de X días"""
    try:
        log_path = ensure_logs_dir(logs_dir)
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 86400)
        
        for log_file in log_path.glob("api_errors_*.txt"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                
    except Exception as e:
        print(f"Error limpiando logs antiguos: {e}")

def format_log_message(log_data: Dict[str, Any]) -> str:
    """Formatear mensaje de log legible"""
    lines = [
        f"TIMESTAMP: {log_data['timestamp']}",
        f"LEVEL: {log_data['level']}",
        f"ERROR_TYPE: {log_data['error_type']}",
        f"MESSAGE: {log_data['error_message']}",
        f"ENDPOINT: {log_data.get('endpoint', 'N/A')}",
        f"USER_ID: {log_data.get('user_id', 'N/A')}",
    ]
    
    if log_data.get('exception_type'):
        lines.append(f"EXCEPTION: {log_data['exception_type']} - {log_data.get('exception_message', '')}")
    
    if log_data.get('request_data'):
        lines.append("REQUEST_DATA:")
        lines.append(json.dumps(log_data['request_data'], indent=2, ensure_ascii=False))
    
    if log_data.get('additional_context'):
        lines.append("ADDITIONAL_CONTEXT:")
        lines.append(json.dumps(log_data['additional_context'], indent=2, ensure_ascii=False))
    
    if log_data.get('traceback'):
        lines.append("TRACEBACK:")
        lines.append(log_data['traceback'])
    
    lines.append("=" * 60)
    lines.append("")
    
    return "\n".join(lines)