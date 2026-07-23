from fastapi import Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Ngoại lệ cơ sở cho các lỗi nghiệp vụ Logistics."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundException(DomainException):
    def __init__(self, message: str = "Không tìm thấy dữ liệu yêu cầu"):
        super().__init__(message=message, code="NOT_FOUND")


class ValidationException(DomainException):
    def __init__(self, message: str = "Dữ liệu đầu vào không hợp lệ"):
        super().__init__(message=message, code="VALIDATION_ERROR")


class RoutingException(DomainException):
    def __init__(self, message: str = "Lỗi khi tính toán định tuyến tuyến đường"):
        super().__init__(message=message, code="ROUTING_ERROR")


class HubSelectionException(DomainException):
    def __init__(self, message: str = "Lỗi khi chạy thuật toán p-Median chọn Hub"):
        super().__init__(message=message, code="HUB_SELECTION_ERROR")


# Global Exception Handler cho FastAPI
async def domain_exception_handler(request: Request, exc: DomainException):
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, NotFoundException):
        status_code = status.HTTP_404_NOT_FOUND

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message
        }
    )
