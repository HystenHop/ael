# Power BI — visão do catálogo

A primeira versão inclui integração por snapshots CSV do SQLite, consultas Power Query
(M), medidas DAX e tema. O relatório PBIX deve ser montado e validado no Power BI
Desktop: esse aplicativo não foi executado no ambiente desta entrega.

## 1. Exportar do banco

Com o banco inicializado e os cadastros prontos, na raiz do AEL:

```powershell
$env:AEL_DATABASE = Join-Path $PWD 'demo.sqlite3'
.\.venv\Scripts\python.exe -m flask --app ael export-bi --output exports/bi-01
```

O comando cria Materiais.csv, Locais.csv, Eventos.csv e manifest.json. Não exporta
usuários, senhas, tokens, endereço dos locais nem conteúdo detalhado da auditoria.
Os nomes e códigos cadastrados continuam sendo dados do seu banco: confira antes de compartilhar.
Cada pasta é um snapshot. Se ocorrer falha de exportação, descarte a pasta incompleta
e repita com novo nome. Não use um snapshot sem manifest.json.

## 2. Importar no Power BI Desktop

1. Abra um relatório vazio. Entre em **Transformar dados** e crie uma **Consulta em branco**.
2. No **Editor Avançado**, cole PastaDados.pq, altere para o caminho absoluto da
   pasta exportada e nomeie a consulta **PastaDados**. Não acrescente barra ao final.
3. Crie mais três consultas em branco, chamadas **Materiais**, **Locais** e **Eventos**.
   Cole o conteúdo do arquivo .pq correspondente no Editor Avançado de cada uma.
4. Se PastaDados estiver com carregamento habilitado, desabilite-o. Mantenha as três
   tabelas carregadas e selecione **Fechar e aplicar**.
5. As tabelas são independentes nesta versão. Não crie relacionamento entre os IDs:
   um ID de material não representa um local, e Eventos contém ambas as entidades.
6. Crie cada medida de Medidas.dax separadamente, na tabela indicada. Não cole o
   arquivo inteiro em uma única medida. Se seu Desktop usa separadores DAX locais,
   adapte as vírgulas conforme a configuração. Formate Percentual ativo como porcentagem.

## 3. Montar uma página

Título: **AEL | Catálogo e atividade**. Subtítulo: **Snapshot local — cadastro e auditoria**.
Em Exibição > Temas, importe Tema-AEL.json.

| Visual | Campos |
|---|---|
| Cartão | Materiais ativos |
| Cartão | Locais ativos |
| Cartão | Total de eventos |
| Barras | Materiais[category] e Total de materiais |
| Linha | Eventos[event_date] e Total de eventos |
| Tabela | Materiais[code], [name], [category], [unit], [active] |

Use segmentação de Materiais[category] somente para os visuais de materiais. Use
Eventos[entity] e Eventos[event_date] para os de auditoria. Como não há relacionamento,
esses filtros não afetam os cartões das outras tabelas — isso é intencional.
Salve como AEL-Catalogo.pbix. O arquivo fica ignorado pelo Git por poder conter dados locais.
Para portfólio, produza capturas usando somente registros fictícios identificados.

## 4. Atualizar e validar

Exporte para exports/bi-02, mude PastaDados e clique Atualizar. Compare quantidades
com manifest.json; a medida de materiais ativos deve contar somente active=1.
Crie um material pela API, exporte novamente e confira o aumento de um material e
um evento create. Desative-o pela interface, reexporte e confira a queda de ativos
sem reduzir o total de materiais. Esses são os testes integrados manuais desta entrega.

O painel descreve cadastros e atividade administrativa, **não saldos, entradas ou saídas**.
Não há atualização automática, Power BI Service, DirectQuery ou PBIX pré-montado.

Referências oficiais:
- https://learn.microsoft.com/pt-br/powerquery-m/csv-document
- https://learn.microsoft.com/pt-br/power-bi/transform-model/desktop-common-query-tasks
