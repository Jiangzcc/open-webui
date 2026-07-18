from fastapi.responses import JSONResponse
from open_webui.extensions.credits.errors import CreditError


def public_credit_error_response(error: CreditError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=error.to_envelope())
