"""Gerenciamento de token de pairing seguro para o Themis Browser Bridge."""
from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from core.runtime_paths import config_dir

TOKEN_FILENAME = "bridge_token.json"


def get_token_path() -> Path:
    base = config_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base / TOKEN_FILENAME


def load_or_create_pairing_token() -> str:
    """Carrega o token de emparelhamento persistido ou gera um novo token seguro."""
    token_file = get_token_path()
    if token_file.is_file():
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("token"):
                return data["token"]
        except Exception:
            pass

    # Gera token criptográfico não previsível de 48 caracteres hex (192 bits de entropia)
    new_token = secrets.token_hex(24)
    payload = {
        "token": new_token,
        "created_at": secrets.token_urlsafe(8),
        "description": "Themis Browser Bridge Pairing Token",
    }
    token_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return new_token


def validate_token(provided_token: str | None) -> bool:
    """Valida se o token fornecido corresponde ao token de pairing local."""
    if not provided_token or not isinstance(provided_token, str):
        return False
    current_token = load_or_create_pairing_token()
    return secrets.compare_digest(provided_token.strip(), current_token.strip())


# ---------------------------------------------------------------------------
# Integração com o Dashboard Auth do Hermes (Token Auth Seam)
# ---------------------------------------------------------------------------

try:
    from hermes_cli.dashboard_auth.base import (
        DashboardAuthProvider,
        LoginStart,
        Session,
        TokenPrincipal,
    )
    from hermes_cli.dashboard_auth.registry import register_global_provider
    from hermes_cli.dashboard_auth.token_auth import register_token_route

    class ThemisBridgeTokenProvider(DashboardAuthProvider):
        """Provedor de autenticação de token exclusivo para o Themis Browser Bridge."""

        name: str = "themis_bridge"
        display_name: str = "Themis Browser Bridge Token Auth"
        supports_password: bool = False
        supports_token: bool = True
        supports_session: bool = False

        def start_login(self, *, redirect_uri: str) -> LoginStart:
            raise NotImplementedError

        def complete_login(
            self, *, code: str, state: str, code_verifier: str, redirect_uri: str
        ) -> Session:
            raise NotImplementedError

        def verify_session(self, *, access_token: str) -> Session | None:
            return None

        def refresh_session(self, *, refresh_token: str) -> Session:
            raise NotImplementedError

        def revoke_session(self, *, refresh_token: str) -> None:
            pass

        def verify_token(self, *, token: str) -> TokenPrincipal | None:
            if validate_token(token):
                return TokenPrincipal(
                    principal="themis_browser_bridge",
                    provider=self.name,
                    scopes=("bridge:ingest", "bridge:status", "bridge:sync"),
                )
            return None

    def setup_hermes_bridge_auth():
        """Registra rotas do bridge e provedor de token isolado no Hermes."""
        register_token_route("/api/plugins/themis/bridge/status")
        register_token_route("/api/plugins/themis/bridge/ingest")
        register_token_route("/api/plugins/themis/bridge/sync/plan")
        register_token_route("/api/plugins/themis/bridge/sync/finish")
        register_token_route("/api/plugins/themis/bridge/sync/zip")
        register_token_route("/api/plugins/themis/bridge/sync/status")
        register_token_route("/api/plugins/themis/bridge/sync/pipeline")
        try:
            register_global_provider(ThemisBridgeTokenProvider())
        except Exception:
            pass

except ImportError:
    ThemisBridgeTokenProvider = None  # type: ignore

    def setup_hermes_bridge_auth():
        pass
