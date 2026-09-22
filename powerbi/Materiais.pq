let
    Fonte = Csv.Document(File.Contents(PastaDados & "\Materiais.csv"),
        [Delimiter=";", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalhos, {
        {"id", Int64.Type},
        {"code", type text},
        {"name", type text},
        {"category", type text},
        {"unit", type text},
        {"active", Int64.Type},
        {"created_at", type datetime}
    }, "en-US")
in
    Tipos
