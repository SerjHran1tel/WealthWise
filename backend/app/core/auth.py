from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
from backend.app.core.config import settings

security = HTTPBasic()

# Простое хранилище сессий в памяти (для локального использования)
active_sessions = set()


def generate_session_token() -> str:
    """Генерирует простой токен сессии"""
    return secrets.token_urlsafe(32)


def verify_password(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Проверяет пароль и возвращает токен сессии.
    Для локального использования используем простую схему: username = "user", password из конфига.
    """
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        settings.APP_PASSWORD.encode("utf8")
    )

    if not correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Генерируем и сохраняем токен
    token = generate_session_token()
    active_sessions.add(token)

    return token


def verify_session(x_session_token: Optional[str] = Header(None)) -> bool:
    """
    Проверяет активность сессии.
    Для упрощения можно отключить, оставив только проверку пароля при входе.
    """
    # Для локального использования можем вообще отключить проверку токена
    # и полагаться только на первоначальную авторизацию
    if not settings.DEBUG:
        if not x_session_token or x_session_token not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

    return True


def logout_session(x_session_token: Optional[str] = Header(None)):
    """Удаляет сессию"""
    if x_session_token and x_session_token in active_sessions:
        active_sessions.remove(x_session_token)


# Для локального использования можем использовать упрощенную версию
# где проверка отключена в DEBUG режиме
def get_current_user() -> str:
    """
    Возвращает ID текущего пользователя.
    Для локального использования всегда один пользователь.
    """
    return settings.DEFAULT_USER_ID


class AuthConfig:
    """Конфигурация авторизации"""

    @staticmethod
    def is_auth_required() -> bool:
        """Требуется ли авторизация (можно настроить в конфиге)"""
        return not settings.DEBUG

    @staticmethod
    def clear_all_sessions():
        """Очистка всех сессий"""
        active_sessions.clear()