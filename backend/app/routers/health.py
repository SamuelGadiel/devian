from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    response_description="Serviço vivo. Sem autenticação (público).",
)
def health():
    """Usado por monitoramento e pelo app para checar conectividade com o hub."""
    return {"status": "ok"}
