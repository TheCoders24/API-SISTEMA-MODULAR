from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict

def sanitize_data(data: Any) -> Any:
    """Convierte datos complejos a formatos seguros para logging (JSON serializable)."""
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return str(data)


def ensure_logs_dir(logs_dir: str) -> Path:
    """Crear carpeta de logs si no existe"""
    path = Path(logs_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_log_file(logs_dir: Path) -> Path:
    """Nombre de archivo de log diario"""
    today = "api_errors_" + datetime.now().strftime("%Y-%m-%d") + ".txt"
    return logs_dir / today


def clean_old_logs(logs_dir: Path, days_to_keep: int):
    """Elimina logs antiguos"""
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    for file in logs_dir.glob("api_errors_*.txt"):
        if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
            file.unlink()


def format_log_message(entry: Dict[str, Any]) -> str:
    """Convierte dict de log a texto legible"""
    parts = [f"{key.upper()}: {value}" for key, value in entry.items() if value is not None]
    return "\n".join(parts) + "\n" + "="*60
