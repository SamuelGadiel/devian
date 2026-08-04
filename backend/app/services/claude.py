"""Executa o Claude Code dentro do container devian (headless)."""

import json
import subprocess

from app.config import settings


class ClaudeError(Exception):
    pass


class ClaudeTimeout(Exception):
    pass


def run_claude(
    prompt: str,
    session_id: str,
    resume: bool = False,
    timeout: int | None = None,
) -> str:
    """Chama `claude -p` no container devian com a sessão indicada.

    Sessão nova: sem --resume. Sessão já existente no container: --resume
    (senão o Claude responde "Session ID ... is already in use").
    """
    cmd = [
        "docker",
        "exec",
        settings.container_devian,
        settings.claude_cmd,
        "-p",
        prompt,
    ]
    if resume:
        # Sessão existente: --resume <id> retoma pelo id (--session-id + --resume
        # exige --fork-session nesta versão, o que quebraria a continuidade)
        cmd += ["--resume", session_id]
    else:
        cmd += ["--session-id", session_id]
    cmd += ["--output-format", "json"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout or settings.claude_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeTimeout("Claude Code demorou demais para responder") from exc

    if proc.returncode != 0:
        raise ClaudeError(proc.stderr[-2000:] or f"exit code {proc.returncode}")

    out = proc.stdout.strip()
    if not out:
        raise ClaudeError("Claude Code não retornou saída")

    # Saída JSON (--output-format json): `result` é string direta
    try:
        data = json.loads(out)
        if data.get("is_error"):
            raise ClaudeError(data.get("error_message") or "Claude Code retornou erro")
        result = data.get("result")
        if isinstance(result, str):
            return result
        if isinstance(result, list):
            texts = [
                item.get("text", "")
                for item in result
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            if texts:
                return "\n".join(texts)
    except json.JSONDecodeError:
        pass

    return out
