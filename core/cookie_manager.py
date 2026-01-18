"""
Gerenciador de cookies para autenticação no X (Twitter).
Permite importar, validar e persistir cookies para uso com Playwright.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CookieManager:
    """Gerencia importação e persistência de cookies do X."""

    def __init__(self, browser_data_dir: str = "./browser_data"):
        """
        Inicializa o gerenciador de cookies.

        Args:
            browser_data_dir: Diretório onde os cookies serão salvos
        """
        self.browser_data_dir = Path(browser_data_dir)
        self.cookies_file = self.browser_data_dir / "cookies.json"

        # Cria o diretório se não existir
        self.browser_data_dir.mkdir(parents=True, exist_ok=True)

    def validate_json_cookies(self, cookies_json: str) -> tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Valida se o JSON de cookies está no formato correto.

        Args:
            cookies_json: String JSON contendo os cookies

        Returns:
            Tupla (válido, mensagem, cookies_processados)
        """
        try:
            cookies = json.loads(cookies_json)
        except json.JSONDecodeError as e:
            return False, f"❌ JSON inválido: {str(e)}", None

        # Valida se é uma lista
        if not isinstance(cookies, list):
            return False, "❌ O JSON deve ser uma lista de cookies", None

        if len(cookies) == 0:
            return False, "❌ A lista de cookies está vazia", None

        # Valida se contém cookies do domínio x.com
        x_cookies = [c for c in cookies if self._is_x_cookie(c)]

        if len(x_cookies) == 0:
            return False, "❌ Nenhum cookie do domínio x.com encontrado", None

        # Valida estrutura básica dos cookies
        required_fields = ['name', 'value', 'domain']
        for cookie in x_cookies:
            if not isinstance(cookie, dict):
                return False, "❌ Cookie com formato inválido (deve ser um objeto)", None

            missing_fields = [f for f in required_fields if f not in cookie]
            if missing_fields:
                return False, f"❌ Cookie faltando campos obrigatórios: {', '.join(missing_fields)}", None

        return True, f"✅ {len(x_cookies)} cookies válidos do X encontrados", x_cookies

    def _is_x_cookie(self, cookie: Dict[str, Any]) -> bool:
        """Verifica se um cookie pertence ao domínio x.com."""
        domain = cookie.get('domain', '')
        return 'x.com' in domain or '.twitter.com' in domain

    def convert_to_playwright_format(self, cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converte cookies do formato de exportação (EditThisCookie/Cookie-Editor)
        para o formato aceito pelo Playwright.

        Args:
            cookies: Lista de cookies no formato de exportação

        Returns:
            Lista de cookies no formato Playwright
        """
        playwright_cookies = []

        for cookie in cookies:
            # Formato Playwright requer campos específicos
            pw_cookie = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.x.com'),
                'path': cookie.get('path', '/'),
            }

            # Campos opcionais
            if 'expirationDate' in cookie:
                # Converte timestamp para formato Playwright
                pw_cookie['expires'] = int(cookie['expirationDate'])
            elif 'expires' in cookie:
                pw_cookie['expires'] = int(cookie['expires'])

            if 'httpOnly' in cookie:
                pw_cookie['httpOnly'] = cookie['httpOnly']

            if 'secure' in cookie:
                pw_cookie['secure'] = cookie['secure']

            if 'sameSite' in cookie:
                # Playwright aceita: 'Strict', 'Lax', 'None'
                same_site = cookie['sameSite']
                if isinstance(same_site, str):
                    pw_cookie['sameSite'] = same_site.capitalize()

            playwright_cookies.append(pw_cookie)

        return playwright_cookies

    def save_cookies(self, cookies: List[Dict[str, Any]]) -> tuple[bool, str]:
        """
        Salva cookies no arquivo de persistência.

        Args:
            cookies: Lista de cookies no formato Playwright

        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            # Adiciona metadados
            cookie_data = {
                'imported_at': datetime.now().isoformat(),
                'cookies': cookies,
                'count': len(cookies)
            }

            # Salva no arquivo
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ {len(cookies)} cookies salvos em {self.cookies_file}")
            return True, f"✅ {len(cookies)} cookies salvos com sucesso"

        except Exception as e:
            logger.error(f"❌ Erro ao salvar cookies: {e}")
            return False, f"❌ Erro ao salvar cookies: {str(e)}"

    def load_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """
        Carrega cookies do arquivo de persistência.

        Returns:
            Lista de cookies no formato Playwright ou None se não houver cookies
        """
        if not self.cookies_file.exists():
            logger.warning("⚠️ Arquivo de cookies não encontrado")
            return None

        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)

            cookies = cookie_data.get('cookies', [])
            imported_at = cookie_data.get('imported_at', 'desconhecido')

            logger.info(f"✅ {len(cookies)} cookies carregados (importados em {imported_at})")
            return cookies

        except Exception as e:
            logger.error(f"❌ Erro ao carregar cookies: {e}")
            return None

    def has_cookies(self) -> bool:
        """Verifica se existem cookies salvos."""
        return self.cookies_file.exists() and self.cookies_file.stat().st_size > 0

    def get_cookies_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre os cookies salvos.

        Returns:
            Dicionário com informações dos cookies
        """
        if not self.has_cookies():
            return {
                'exists': False,
                'count': 0,
                'imported_at': None,
                'file_path': str(self.cookies_file)
            }

        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)

            return {
                'exists': True,
                'count': cookie_data.get('count', 0),
                'imported_at': cookie_data.get('imported_at'),
                'file_path': str(self.cookies_file),
                'cookies': cookie_data.get('cookies', [])
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações dos cookies: {e}")
            return {
                'exists': False,
                'count': 0,
                'imported_at': None,
                'file_path': str(self.cookies_file),
                'error': str(e)
            }

    def delete_cookies(self) -> tuple[bool, str]:
        """
        Remove os cookies salvos.

        Returns:
            Tupla (sucesso, mensagem)
        """
        if not self.cookies_file.exists():
            return True, "ℹ️ Nenhum cookie para remover"

        try:
            self.cookies_file.unlink()
            logger.info("✅ Cookies removidos com sucesso")
            return True, "✅ Cookies removidos com sucesso"
        except Exception as e:
            logger.error(f"❌ Erro ao remover cookies: {e}")
            return False, f"❌ Erro ao remover cookies: {str(e)}"

    def import_cookies(self, cookies_json: str) -> tuple[bool, str]:
        """
        Processo completo de importação de cookies.

        Args:
            cookies_json: String JSON com os cookies exportados

        Returns:
            Tupla (sucesso, mensagem)
        """
        # 1. Valida o JSON
        valid, msg, cookies = self.validate_json_cookies(cookies_json)
        if not valid:
            return False, msg

        # 2. Converte para formato Playwright
        pw_cookies = self.convert_to_playwright_format(cookies)

        # 3. Salva os cookies
        success, save_msg = self.save_cookies(pw_cookies)

        if success:
            return True, f"✅ Importação concluída! {len(pw_cookies)} cookies salvos"
        else:
            return False, save_msg
