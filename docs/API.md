# API de materiais

A API JSON compartilha o administrador, a sessão, as validações e a auditoria da
interface web. Escopo da v0.1.1: leitura e criação de materiais. Não inclui tokens
JWT, acesso anônimo, edição, exclusão ou integração entre servidores.

| Método | Rota | Resultado |
|---|---|---|
| GET | `/api/csrf` | Token CSRF para a sessão autenticada |
| GET | `/api/materiais` | Lista paginada; ativos por padrão |
| GET | `/api/materiais/<id>` | Um material, inclusive inativo |
| POST | `/api/materiais` | Cria material e auditoria na mesma transação |

## Autenticação

Use o formulário `/login` e preserve o cookie de sessão. Para criar um material,
consulte `/api/csrf` e envie seu token no cabeçalho `X-CSRFToken`.
O token do login deve ser obtido novamente após autenticar, pois a sessão é renovada.
Não há CORS habilitado nem endpoint público de cadastro de usuários.

## Exemplo completo no PowerShell

Com o AEL rodando em `http://127.0.0.1:5000`, execute em outro terminal.
Use as credenciais do administrador que você criou; nenhuma senha é fixada no código.

```powershell
$base = 'http://127.0.0.1:5000'
$login = Invoke-WebRequest "$base/login" -SessionVariable aelSession -UseBasicParsing
$csrfLogin = [regex]::Match($login.Content, 'name="csrf_token" value="([^"]+)"').Groups[1].Value
$credentials = Get-Credential -Message 'Administrador do AEL'
$body = @{
    username = $credentials.UserName
    password = $credentials.GetNetworkCredential().Password
    csrf_token = $csrfLogin
}
Invoke-WebRequest "$base/login" -Method Post -WebSession $aelSession -Body $body -UseBasicParsing | Out-Null
$body.Clear()
$credentials = $null

Invoke-RestMethod "$base/api/materiais?per_page=10&page=1" -WebSession $aelSession
$csrf = Invoke-RestMethod "$base/api/csrf" -WebSession $aelSession
$payload = @{code='API-001'; name='Luva de trabalho'; category='EPI'; unit='PAR'} | ConvertTo-Json
$created = Invoke-RestMethod "$base/api/materiais" -Method Post -WebSession $aelSession -ContentType 'application/json; charset=utf-8' -Headers @{'X-CSRFToken'=$csrf.csrf_token} -Body ([System.Text.Encoding]::UTF8.GetBytes($payload))
Invoke-RestMethod "$base/api/materiais/$($created.data.id)" -WebSession $aelSession
```

Execute a criação uma vez por código; repetir `API-001` retorna conflito 409.
Os comandos acima também criam um material real no seu banco local. Use banco de
estudo para experimentar. Nunca grave senhas no README, em scripts ou no Git.

## Contrato

POST exige somente quatro campos de texto: `code`, `name`, `category`, `unit`.
As regras são as mesmas do cadastro web. Código é convertido para maiúsculas;
categorias e unidades disponíveis estão em `ael/services.py`.

Resposta de criação: **201**, cabeçalho `Location` e objeto `data` com o cadastro.
Resposta da listagem:

```json
{"data": [], "pagination": {"page": 1, "per_page": 20, "total": 0}}
```

Filtros: `q` (até 100 caracteres, busca literal por nome/código),
`status=active|inactive|all`, `page` (1 a 1000000), `per_page` (1 a 100).
Uma página além do total retorna lista vazia. A ordenação é por nome e ID.
O campo `active` é booleano JSON. Datas geradas pelo SQLite estão em UTC.

Erros têm formato `{"error":{"code":"...","message":"..."}}`:

- 400: conteúdo, filtros, validação ou CSRF inválidos;
- 401: sessão ausente, expirada ou usuário desativado;
- 403: usuário autenticado sem perfil de administrador;
- 404: recurso inexistente;
- 405: método não suportado;
- 409: código de material já existente;
- 413: corpo excedendo 64 KiB;
- 415: corpo não enviado como JSON.

A proteção CSRF é verificada antes da autorização nas requisições de escrita.
Uma escrita sem sessão e sem token pode retornar 400 antes de retornar 401.
As respostas mantêm `Cache-Control: no-store` e os cabeçalhos de segurança da aplicação.

## Testes

`python -m pytest` executa o catálogo web e a API. Os testes da API cobrem autorização,
CSRF, tipos JSON, paginação, busca literal, duplicatas, auditoria atômica e erros HTTP.
A API não muda as tabelas nem exige migração adicional.
