"""Loopback API with a bounded body; health never touches checkpoint files."""

from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from . import __version__
from .inference import ProviderError
from .schemas import Prediction, PredictRequest
from .service import TriageService

MAX_BODY_BYTES = 64_000


class BodyLimitMiddleware:
    """Bound bytes before JSON parsing, including chunked bodies without Content-Length."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > MAX_BODY_BYTES:
                response = JSONResponse({"detail": "Request body exceeds 64000 bytes"}, 413)
                return await response(scope, receive, send)
            chunks.append(message)
            if not message.get("more_body", False):
                break
        index = 0

        async def replay():
            nonlocal index
            if index < len(chunks):
                message = chunks[index]
                index += 1
                return message
            return await receive()

        await self.app(scope, replay, send)


def create_app(service: TriageService | None = None) -> FastAPI:
    service = service or TriageService()
    application = FastAPI(title="Kubernetes Incident Triage", version=__version__)
    application.add_middleware(BodyLimitMiddleware)

    @application.get("/health")
    def health():
        return {
            "status": "ok",
            "version": __version__,
            "review_required": True,
            "laya_loaded": service.laya.loaded,
            "model": service.laya.model,
            "model_revision": service.laya.revision,
            "downloads_allowed": service.laya.allow_download,
        }

    @application.post("/predict", response_model=Prediction)
    def predict(request: PredictRequest):
        try:
            return service.predict(request.incident, request.provider)
        except ProviderError as exc:
            status = 502 if exc.code in {"invalid_response", "inference_failed"} else 503
            raise HTTPException(
                status_code=status,
                detail={
                    "code": exc.code,
                    "message": str(exc),
                    "review_status": "required",
                    "raw_response": exc.raw_response,
                    "inference_ms": exc.inference_ms,
                },
            ) from exc

    return application


app = create_app()
