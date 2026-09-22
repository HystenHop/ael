# Fluxo da aplicação

## Cadastro de um material

1. O navegador solicita `/catalog/materials/new`.
2. `auth.py` carrega o usuário da sessão e verifica se o perfil ativo é administrador.
3. `catalog.py` renderiza o formulário `templates/edit.html`.
4. O envio do formulário inclui os dados e o token CSRF.
5. `services.py` valida código, nome, categoria e unidade no servidor.
6. Uma transação grava o material e o evento de auditoria.
7. Se qualquer gravação falhar, toda a operação é desfeita.
8. A resposta redireciona para a listagem atualizada.

## Responsabilidades

| Camada | Papel |
|---|---|
| Rotas | Receber a requisição, conferir o contexto e formar a resposta |
| Serviços | Aplicar validações e regras de negócio |
| Persistência | Executar SQL parametrizado, transações e migrações |
| Templates | Apresentar dados já preparados pelo servidor |
| Testes | Verificar regras, erros, permissões e integridade |

## Decisões de integridade

- O banco reforça restrições que também existem no formulário.
- Alteração e auditoria pertencem à mesma transação.
- O campo `version` detecta tentativas de salvar um formulário desatualizado.
- Cadastros são desativados em vez de apagados, preservando identidade e histórico.
- Os nomes de tabelas usados dinamicamente vêm de uma lista fechada; valores de
  entrada são enviados ao SQLite como parâmetros.
