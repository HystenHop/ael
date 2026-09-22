let
    Fonte = Csv.Document(File.Contents(PastaDados & "\Eventos.csv"),
        [Delimiter=";", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),
    Tipos = Table.TransformColumnTypes(Cabecalhos, {
        {"id", Int64.Type},
        {"entity_key", type text},
        {"entity", type text},
        {"action", type text},
        {"event_date", type date},
        {"created_at", type datetime}
    }, "en-US")
in
    Tipos
