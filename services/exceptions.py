class ServiceError(Exception):
    status_code: int = 400

class DocumentNotFound(ServiceError):
    status_code = 404

class DocumentNotReady(ServiceError):
    status_code = 409

class FileTooLarge(ServiceError):
    status_code = 413

class InvalidFileType(ServiceError):
    status_code = 400

class IngestionFailed(ServiceError):
    status_code = 422

class QuotaExceeded(ServiceError):
    status_code = 429