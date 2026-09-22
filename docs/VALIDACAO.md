# Validação da versão 0.1.1

## Ambiente

Validação executada em Windows com Python 3.13.1 em `.venv`, SQLite isolado em
`instance/integration-demo.sqlite3` e dados fictícios. O banco demonstrativo não
faz parte do pacote público. Nenhuma alteração foi publicada no GitHub.

## Testes executados e aprovados

| Verificação | Resultado |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q` | **72 testes passaram** |
| `.venv\Scripts\python.exe -m ruff check .` | **Aprovado** |
| `.venv\Scripts\python.exe -m ruff format --check .` | **17 arquivos formatados** |
| Login válido e painel | Aprovado, HTTP 200 |
| CSRF e listagem API com e sem barra | Aprovado |
| Criação API com sessão e CSRF | Aprovado, HTTP 201 |
| Duplicidade, CSRF ausente e recurso inexistente | Aprovados conforme contrato |
| Cadastro, pesquisa e edição web | Aprovado |
| Versão desatualizada | Bloqueada, HTTP 400 |
| Desativação e reativação | Aprovadas |
| Cadastro de local | Aprovado |
| Auditoria | Eventos visíveis no painel e nos CSVs |
| Logout e acesso posterior | Redirecionamento para login |
| Exportação BI snapshot 1 | 8 materiais, 15 eventos |
| Exportação BI snapshot 2 após desativação | 8 materiais, 16 eventos, 7 ativos |

A exportação confirmou que desativar um material reduz os ativos sem reduzir o
total de materiais. O material criado pela API apareceu com dois eventos no
snapshot final: cadastro e desativação.

## Problemas corrigidos

- Adicionada a variável opcional `AEL_DATABASE` para selecionar um banco
  demonstrativo sem tocar no banco padrão ou em outros projetos.
- Incluído teste de regressão para essa configuração.
- Ajustada a documentação de execução e exportação para banco isolado.
- Corrigida a formatação do teste novo.

## Verificações não executadas

- Power BI Desktop não foi encontrado nesta máquina.
- Consultas Power Query, medidas DAX, tema, layout visual e atualização dentro
  do Desktop não foram executados.
- Inspeção visual automatizada por navegador não foi repetida nesta execução.

## Ações manuais restantes

1. No Power BI Desktop, importar as consultas de `powerbi/`, ajustar `PastaDados`
   para `exports/bi-integration-03` e aplicar os tipos das colunas.
2. Criar as medidas de `powerbi/Medidas.dax`, importar `Tema-AEL.json` e montar
   a página **Catálogo e atividade** conforme `powerbi/README.md`.
3. Atualizar para `exports/bi-integration-04` e conferir os indicadores.
4. Salvar um `.pbix` somente após essa atualização ser confirmada. Nenhum PBIX
   foi fabricado ou incluído nesta entrega.

O painel representa cadastro e atividade administrativa; não representa saldo,
entrada, saída ou movimentação de estoque.
