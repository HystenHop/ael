# Validação da versão 0.1

Execução em 21/09/2026, em ambiente Linux com Python 3.12.

## Resultados executados

| Verificação | Resultado |
|---|---|
| `python -m pytest -q` | 44 testes passaram (última execução: 10,20 s) |
| `python -m ruff check .` | Todos os checks passaram |
| `python -m ruff format --check .` | 12 arquivos Python formatados |
| Migração 001 → 002 em banco existente | Passou; registro anterior preservado |
| Reaplicação de migrações | Passou; sem duplicação de versão |
| Falha em migração | Passou; alteração desfeita e versão não registrada |
| Falha na auditoria | Passou; cadastro também desfeito |
| Browser Chromium / Playwright 1.55.0 | Fluxo descrito abaixo passou |

Os testes de backend verificam casos válidos e inválidos, permissões de todos os
perfis previstos, sessões de usuários desativados, CSRF, hash de senha,
escapamento de HTML, busca, unicidade, histórico, edição desatualizada e CLI.

## Fluxo no navegador

Com banco descartável, senha gerada e dados fictícios:

1. Login e abertura do painel.
2. Listagem dos quatro materiais demonstrativos.
3. Cadastro e edição de um material.
4. Desativação e reativação com confirmação.
5. Busca pelo código criado, retornando somente uma linha.
6. Cadastro de local e conferência da listagem.
7. Visualização em 1440 × 1050 e 390 × 844.
8. Verificação de ausência de transbordamento horizontal da página em celular
   no painel, lista e formulário. A tabela permite rolagem horizontal interna.
9. Logout e bloqueio ao tentar abrir uma página protegida.
10. Nenhum erro JavaScript capturado durante o fluxo.

O script reproduzível está em `scripts/check_browser.py`. Ele requer Playwright
como ferramenta opcional; não é dependência da aplicação nem da suíte pytest.
Ele usa banco temporário e grava capturas em `docs/capturas`.

As capturas de login, painel, listagem e celular foram inspecionadas visualmente.
Não foi realizada auditoria formal de acessibilidade.

## Ambiente de dependências observado

Flask 3.1.2, Flask-WTF 1.2.2, Werkzeug 3.1.8, Jinja2 3.1.6,
pytest 8.4.2 e Ruff 0.13.1. Dependências transitivas podem variar em nova instalação.

## Estado real de conclusão

- **Implementada:** fundação e catálogo da etapa 1.
- **Testada:** suíte automatizada, navegador e inspeção visual.
- **GitHub Actions:** workflow configurado para push e pull request.
- **Publicação:** código-fonte disponível no GitHub; demonstração online ainda não realizada.

Testes locais não comprovam capacidade de produção, adequação offshore ou
atendimento a operações críticas. A revisão de implantação permanece fora desta etapa.
