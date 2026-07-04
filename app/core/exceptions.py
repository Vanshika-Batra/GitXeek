from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


def not_found(resource: str = "Resource") -> AppException:
    return AppException(status.HTTP_404_NOT_FOUND, f"{resource} not found")


def conflict(message: str) -> AppException:
    return AppException(status.HTTP_409_CONFLICT, message)


def unauthorized(message: str = "Invalid credentials") -> AppException:
    return AppException(status.HTTP_401_UNAUTHORIZED, message)


def forbidden(message: str = "Forbidden") -> AppException:
    return AppException(status.HTTP_403_FORBIDDEN, message)


def bad_request(message: str) -> AppException:
    return AppException(status.HTTP_400_BAD_REQUEST, message)
