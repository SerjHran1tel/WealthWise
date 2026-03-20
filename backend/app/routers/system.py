import time
import psutil
import platform
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.agents.rag_classifier import rag_classifier

router = APIRouter(prefix="/api/system", tags=["system"])

# Время запуска сервера
_start_time = time.time()


@router.get("/stats")
async def system_stats():
    """Анализ вычислительных потребностей системы."""
    process = psutil.Process()
    vm = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)

    uptime_sec = int(time.time() - _start_time)
    cache_stats = rag_classifier.get_cache_stats()

    return {
        "hardware": {
            "ram_used_mb": round(process.memory_info().rss / 1024 ** 2, 1),
            "ram_total_mb": round(vm.total / 1024 ** 2, 1),
            "ram_available_mb": round(vm.available / 1024 ** 2, 1),
            "ram_percent": vm.percent,
            "cpu_percent": cpu,
            "cpu_cores": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(logical=True),
            "platform": platform.system(),
        },
        "model": {
            "name": settings.OLLAMA_MODEL,
            "inference": "local (Ollama)",
            "api_calls": 0,  # 100% локально
            "privacy": "100% on-device",
        },
        "cache": {
            "rag_entries": cache_stats.get("size", 0),
            "rag_max_size": cache_stats.get("max_size", 5000),
            "rag_ttl_minutes": 30,
        },
        "uptime_seconds": uptime_sec,
        "minimum_requirements": {
            "ram_gb": 4,
            "storage_gb": 8,
            "cpu_cores": 2,
            "notes": "Протестировано на AMD Ryzen 5 (CPU-only). "
                     "Совместимо с Raspberry Pi 5 (8GB).",
        },
        "optimization_features": [
            "Малая модель: qwen3.5/qwen2.5 (2b–7b параметров)",
            "TTL-кэш RAG: повторные транзакции не идут в LLM",
            "Rule-based fallback: быстрое правило вместо LLM",
            "Потоковый парсер CSV: O(1) по памяти",
            "APScheduler: фоновые задачи без блокировки API",
        ],
    }


@router.get("/health")
async def health_check():
    """Быстрая проверка работоспособности."""
    return {
        "status": "ok",
        "model": settings.OLLAMA_MODEL,
        "uptime_seconds": int(time.time() - _start_time),
    }
