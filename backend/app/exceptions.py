"""Excepciones personalizadas para la API."""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Error para fallos de autenticación."""

    def __init__(self, detail: str = "Credenciales inválidas") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class JohnDeereServiceError(HTTPException):
    """Error cuando la API de John Deere no responde correctamente."""

    def __init__(self, detail: str = "Error al comunicarse con John Deere") -> None:
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


class ValidationError(HTTPException):
    """Error para validaciones de usuario."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

