"""Validação de ID tokens do Google — sem Firebase.

O app (google_sign_in) devolve um ID token (JWT) assinado pelo Google.
Aqui validamos a assinatura contra o JWKS público do Google e conferimos
`aud` (== nosso client id), `iss` e `exp`. O retorno são os claims
(sub, email, name, picture...).
"""

from collections.abc import Mapping

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token


class GoogleTokenError(ValueError):
    """ID token do Google inválido, expirado ou com claims inesperados."""


def verify_google_id_token(token: str, client_id: str) -> Mapping[str, object]:
    """Valida o ID token e devolve os claims do Google.

    Lança `GoogleTokenError` se a assinatura falhar, o `aud` não bater com
    `client_id`, o token estiver expirado ou o e-mail não verificado.
    """
    try:
        info = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
    except ValueError as exc:
        raise GoogleTokenError(str(exc)) from exc

    if info.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleTokenError("Issuer inesperado no ID token")
    if not info.get("email_verified"):
        raise GoogleTokenError("E-mail não verificado no Google")
    return info
