"""Optional smoke check; uses a disposable database and randomly generated credentials.

Install playwright==1.55.0, then run `python -m playwright install chromium`.
From the project root: python scripts/check_browser.py
"""

import logging
import secrets
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import expect, sync_playwright
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ael import create_app  # noqa: E402
from ael.db import get_db, migrate  # noqa: E402
from ael.services import seed_examples  # noqa: E402


def main():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    with TemporaryDirectory() as directory:
        password = secrets.token_urlsafe(24)
        app = create_app(
            {
                "TESTING": True,
                "DATABASE": str(Path(directory) / "ui.sqlite3"),
                "SECRET_KEY": secrets.token_hex(32),
            }
        )
        with app.app_context():
            migrate(get_db())
            with get_db() as connection:
                connection.execute(
                    "INSERT INTO users(username,password_hash,role) VALUES ('admin',?,'admin')",
                    (generate_password_hash(password),),
                )
            seed_examples("admin")
        server = make_server("127.0.0.1", 0, app)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        shots = Path("docs/capturas")
        shots.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as driver:
                browser = driver.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1050})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base)
                page.screenshot(path=str(shots / "login.png"), full_page=True)
                page.get_by_label("Usuário", exact=True).fill("admin")
                page.get_by_label("Senha", exact=True).fill(password)
                page.get_by_role("button", name="Entrar no AEL").click()
                expect(page.get_by_role("heading", name="Visão geral")).to_be_visible()
                page.screenshot(path=str(shots / "painel.png"), full_page=True)
                page.get_by_role("navigation").get_by_role("link", name="Materiais").click()
                expect(page.locator("tbody tr")).to_have_count(4)
                page.screenshot(path=str(shots / "materiais.png"), full_page=True)
                page.get_by_role("link", name="+ Novo material").click()
                page.get_by_label("SKU / Código").fill("EPI-TESTE")
                page.get_by_label("Nome", exact=True).fill("Óculos de proteção")
                page.get_by_label("Categoria", exact=True).select_option("EPI")
                page.get_by_label("Unidade de medida").select_option("UN")
                page.get_by_role("button", name="Salvar cadastro").click()
                expect(page.get_by_role("status")).to_contain_text("sucesso")
                page.get_by_role("link", name="Editar Óculos de proteção", exact=True).click()
                page.get_by_label("Nome", exact=True).fill("Óculos de proteção transparente")
                page.get_by_role("button", name="Salvar cadastro").click()
                page.on("dialog", lambda dialog: dialog.accept())
                page.get_by_role(
                    "button", name="Desativar Óculos de proteção transparente", exact=True
                ).click()
                expect(
                    page.get_by_role("row").filter(has_text="Óculos de proteção transparente")
                ).to_contain_text("Inativo")
                page.get_by_role(
                    "button", name="Reativar Óculos de proteção transparente", exact=True
                ).click()
                page.get_by_label("Buscar por nome ou código").fill("EPI-TESTE")
                page.get_by_role("button", name="Filtrar", exact=True).click()
                expect(page.locator("tbody tr")).to_have_count(1)
                page.get_by_role("navigation").get_by_role(
                    "link", name="Locais de armazenagem"
                ).click()
                page.get_by_role("link", name="+ Novo local").click()
                page.get_by_label("Código do local").fill("BASE-TESTE")
                page.get_by_label("Nome", exact=True).fill("Estante C")
                page.get_by_label("Endereço de armazenagem").fill("Corredor C / Estante 02")
                page.get_by_role("button", name="Salvar cadastro").click()
                expect(page.locator("tbody tr")).to_have_count(3)
                page.get_by_role("navigation").get_by_role("link", name="Visão geral").click()
                page.set_viewport_size({"width": 390, "height": 844})
                page.screenshot(path=str(shots / "celular.png"), full_page=True)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.get_by_role("navigation").get_by_role("link", name="Materiais").click()
                expect(page.get_by_role("link", name="+ Novo material")).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.get_by_role("link", name="+ Novo material").click()
                expect(page.get_by_role("button", name="Salvar cadastro")).to_be_visible()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.get_by_role("button", name="Sair", exact=True).click()
                expect(page.get_by_role("heading", name="Acesse sua operação")).to_be_visible()
                page.goto(base + "/catalog/materials")
                expect(page).to_have_url(base + "/login")
                assert not errors, errors
                browser.close()
            print("Browser: login, cadastros, edição, situação, filtro, celular e logout: OK")
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    main()
