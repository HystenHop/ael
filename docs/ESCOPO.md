# Etapa 1 — problema, requisitos e aceite

## Cenário fictício

Maré Apoio: pequena prestadora de serviços com um almoxarifado em terra. Equipes
podem futuramente receber materiais para atividades externas e embarcações.
Nesta etapa só organizamos o cadastro; nenhum envio é realizado pelo sistema.

Fluxo atual suposto: alguém procura um material em uma planilha, interpreta o
nome e pergunta a outra pessoa onde está guardado. Nomes repetidos e endereços
imprecisos tornam essa consulta frágil. Essa descrição é uma hipótese didática,
sem entrevista de descoberta com usuários reais.

Fluxo entregue: administrador entra, cadastra códigos únicos, define nomes,
unidades e endereços, pesquisa e corrige cadastros mantendo histórico.

## Usuários

| Perfil | Etapa 1 | Etapas posteriores |
|---|---|---|
| Administrador | Acesso e manutenção dos cadastros | Gestão de acessos e configuração |
| Almoxarife | Sem acesso funcional | Entradas, saídas, separação |
| Solicitante | Sem acesso funcional | Solicitar e acompanhar materiais |
| Aprovador | Sem acesso funcional | Aprovar/rejeitar solicitações |

## Critérios de aceite

| Requisito | Resultado verificável |
|---|---|
| Catálogo de materiais | Salvar SKU, nome, categoria e unidade; listar e editar |
| Catálogo de locais | Salvar código, nome e endereço; listar e editar |
| Unicidade | Bloquear código repetido, inclusive em minúsculas |
| Validação | Rejeitar campos vazios, comprimentos inválidos e opções não permitidas |
| Pesquisa | Buscar código/nome; filtrar ativos, inativos e todos |
| Preservação | Desativar e reativar; não disponibilizar exclusão física |
| Responsabilidade | Gravar autor e instantâneos antes/depois da alteração |
| Atomicidade | Não manter alteração sem o respectivo histórico |
| Acesso | Exigir administrador ativo em cada leitura/alteração protegida |
| CSRF | Rejeitar alterações sem token válido, inclusive login/logout |
| Atualização | Aplicar migração a banco existente preservando registros |
| Uso local | Abrir sem debug somente no endereço de loopback |
| Interface | Navegação, formulário e listagem utilizáveis em desktop e celular |

## Vocabulário do estoque futuro

- **Saldo físico**: quantidade registrada em um local.
- **Saldo reservado**: parcela desse saldo comprometida com solicitações.
- **Saldo disponível**: saldo físico menos reservado.

Nenhum desses valores é armazenado ou calculado nesta versão. A contagem do
painel representa **cadastros ativos**, não unidades físicas disponíveis.
Quando as quantidades forem introduzidas, será definida precisão por unidade e
representação exata (sem float). Materiais em trânsito exigirão regra própria.


## Complemento 0.1.1

API REST autenticada para consulta e criação de materiais, com paginação e CSRF.
Exportação do SQLite para Power BI, consultas M, medidas DAX e tema.
Foco em prática, estudo e revisão dos processos de back-end, dados e análise.
Sem movimentações de estoque, troca de banco ou novo framework nesta revisão.
