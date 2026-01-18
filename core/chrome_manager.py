"""Gerenciador do Chrome/Chromium para coleta de dados do X."""
import subprocess
import time
import os
from pathlib import Path
from typing import Tuple


def is_chrome_running() -> bool:
    """Verifica se o Chrome está rodando na porta 9222."""
    try:
        result = subprocess.run(
            ["lsof", "-i", ":9222"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def get_chrome_status() -> Tuple[bool, str]:
    """
    Retorna status do Chrome.

    Returns:
        Tupla (está_rodando, mensagem)
    """
    if is_chrome_running():
        try:
            # Tentar obter PID
            result = subprocess.run(
                ["lsof", "-ti", ":9222"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                pid = result.stdout.strip().split()[0]
                return True, f"Rodando (PID: {pid})"
            return True, "Rodando"
        except Exception:
            return True, "Rodando"
    return False, "Parado"


def start_chrome() -> Tuple[bool, str]:
    """
    Inicia o Chrome usando o script start_chrome.sh.

    Returns:
        Tupla (sucesso, mensagem)
    """
    # Verificar se já está rodando
    if is_chrome_running():
        return True, "Chrome já está rodando na porta 9222"

    # Caminho do script
    script_path = Path(__file__).parent.parent / "start_chrome.sh"

    if not script_path.exists():
        return False, f"Script não encontrado: {script_path}"

    try:
        # Executar script em background
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(script_path.parent)
        )

        # Aguardar um pouco
        time.sleep(2)

        # Verificar se iniciou
        if is_chrome_running():
            return True, "Chrome iniciado com sucesso! ✅"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            # Ler log do Chrome se disponível
            log_path = Path("/tmp/chrome.log")
            if log_path.exists():
                try:
                    with open(log_path, "r") as f:
                        chrome_log = f.read()[-500:]  # Últimas 500 chars
                        error_msg = f"{error_msg}\n\nLog do Chrome:\n{chrome_log}"
                except Exception:
                    pass
            return False, f"Chrome não iniciou. Erro: {error_msg}"

    except subprocess.TimeoutExpired:
        # Mesmo com timeout, verificar se iniciou
        if is_chrome_running():
            return True, "Chrome iniciado (processo em background)"
        return False, "Timeout ao iniciar Chrome"

    except Exception as e:
        return False, f"Erro ao executar script: {str(e)}"


def stop_chrome() -> Tuple[bool, str]:
    """
    Para o Chrome/Chromium.

    Returns:
        Tupla (sucesso, mensagem)
    """
    if not is_chrome_running():
        return True, "Chrome já estava parado"

    try:
        # Tentar parar gracefully
        subprocess.run(
            ["pkill", "-f", "chrome.*--remote-debugging-port=9222"],
            timeout=5
        )

        time.sleep(2)

        # Verificar se parou
        if not is_chrome_running():
            return True, "Chrome parado com sucesso"

        # Se ainda estiver rodando, forçar
        subprocess.run(
            ["pkill", "-9", "-f", "chrome.*--remote-debugging-port=9222"],
            timeout=5
        )

        time.sleep(1)

        if not is_chrome_running():
            return True, "Chrome parado (forçado)"

        return False, "Chrome não parou completamente"

    except Exception as e:
        return False, f"Erro ao parar Chrome: {str(e)}"


def restart_chrome() -> Tuple[bool, str]:
    """
    Reinicia o Chrome.

    Returns:
        Tupla (sucesso, mensagem)
    """
    # Parar
    stop_success, stop_msg = stop_chrome()
    if not stop_success and is_chrome_running():
        return False, f"Falha ao parar Chrome: {stop_msg}"

    # Aguardar
    time.sleep(2)

    # Iniciar
    start_success, start_msg = start_chrome()
    return start_success, start_msg


def get_chrome_log() -> str:
    """Retorna o log do Chrome se disponível."""
    log_path = Path("/tmp/chrome.log")
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler log: {str(e)}"
    return "Log não disponível"
