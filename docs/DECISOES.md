# Escolhas da implementação v0.1

Este documento registra as escolhas técnicas da v0.1, seus motivos e as
consequências conhecidas. Ele deve ser atualizado quando uma decisão for revista.

| Escolha | Motivo | Limite/consequência |
|---|---|---|
| Flask + SQLite | Seguir a preferência inicial e facilitar execução local | Rever PostgreSQL na implantação/concorrência real |
| HTML renderizado no servidor | Deixar o fluxo de dados legível e reduzir ferramentas | Não é uma SPA; filtros e gravações recarregam páginas |
| Login administrativo inicial | Proteger o catálogo desde a primeira etapa | Perfis de negócio e gestão de usuários ficam para a etapa 3 |
| Unidades/categorias fixas | Recorte simples para um catálogo inicial | Não há CRUD de categorias ou conversões |
| SKU/código imutável após criar | Evitar mudar a identidade operacional silenciosamente | Corrigir um código exige desativar e cadastrar outro; rever futuramente |
| Desativação no lugar de exclusão | Preservar referências e histórico | Código não pode ser reaproveitado por outro cadastro |
| Auditoria na mesma transação | Impedir gravações sem responsabilidade registrada | Não é trilha inviolável contra acesso direto ao banco |
| Campo version | Impedir que uma aba antiga apague a edição feita por outra | Usuário reabre o cadastro; não há fusão automática de campos |
| Migrações SQL numeradas | Evoluir o esquema sem reinicializar dados | Só avanço; rollback de schema/backup ainda fora do escopo |
| Índice na segunda migração | Acelerar futura consulta de histórico por entidade | Permite testar uma atualização real de banco anterior |
| Sem saldo na etapa 1 | Não exibir números sem movimentações que os expliquem | Catálogo não responde ainda quanto há em estoque |

## Segurança e limitações a tratar antes de implantar

Limite de tentativas de login, recuperação de acesso, servidor de produção,
HTTPS, gestão de segredos, backup/restauração, logs operacionais, revisão de
dependências e testes de carga ainda precisam de trabalho. Nenhuma verificação
de vulnerabilidades de dependências foi realizada nesta entrega.

As dependências principais estão fixadas. As transitivas não estão travadas em
um lockfile; resolução futura pode variar. O ambiente verificado foi registrado
em VALIDACAO.md. A chave local tem permissão 0600 em ambientes POSIX; isso não
substitui uma análise de ACLs no Windows.

A demonstração pode ser repetida e preserva os códigos existentes. Cada cadastro
é uma transação própria: uma falha pode deixar parte dos exemplos criada; repetir
o comando conclui os faltantes. Não deve ser executada simultaneamente.

Antes de introduzir movimentações, revisar possibilidade de alterar unidade,
associação material/local, precisão das quantidades, histórico e permissões.


## API e BI

A API usa a mesma sessão e camada de serviços dos formulários.
A exportação para BI usa uma transação de leitura SQLite e arquivos CSV UTF-8;
o Power BI trabalha com snapshots, sem acesso às credenciais da aplicação.
A análise cobre cadastros e auditoria, não saldos. Não é necessário adicionar
MySQL, PHP ou Node.js para esse recorte.
