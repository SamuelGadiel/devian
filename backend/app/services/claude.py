"""Executa o Claude Code dentro do container devian (headless)."""

import json
import subprocess

from app.config import settings


class ClaudeError(Exception):
    pass


class ClaudeTimeout(Exception):
    pass


def _dir_exists_in_container(path: str) -> bool:
    """Checa se um diretório existe dentro do container devian."""
    try:
        proc = subprocess.run(
            ["docker", "exec", settings.container_devian, "test", "-d", path],
            capture_output=True,
            timeout=10,
        )
        return proc.returncode == 0
    except Exception:
        return False


def resolve_workdir(project) -> str | None:
    """Resolve o workdir do Claude no container para um projeto.

    Interno — usa o `container_path` salvo se existir no container; senão
    tenta `/workspace/<name>`; senão roda sem workdir (raiz).
    """
    candidates: list[str] = []
    if project.container_path:
        candidates.append(project.container_path)
    candidates.append(f"/workspace/{project.name}")
    for candidate in candidates:
        if _dir_exists_in_container(candidate):
            return candidate
    return None


def run_claude(
    prompt: str,
    session_id: str,
    resume: bool = False,
    timeout: int | None = None,
    workdir: str | None = None,
) -> str:
    """Chama `claude -p` no container devian com a sessão indicada.

    Sessão nova: sem --resume. Sessão já existente no container: --resume
    (senão o Claude responde "Session ID ... is already in use").
    workdir: diretório dentro do container (ex: /workspace/sisvisa-serr-mobile)
    para carregar a camada do projeto (CLAUDE.md / .claude).
    """
    cmd = ["docker", "exec"]
    if workdir:
        cmd += ["-w", workdir]
    cmd += [settings.container_devian, settings.claude_cmd, "-p", prompt]
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
