# Projeto Boletim Focus — BCB

## Objetivo

Baixar automaticamente toda segunda-feira o Boletim Focus do Banco Central do Brasil (em PDF), extrair o texto completo e gerar um resumo executivo em Markdown.

## Fonte

- Página oficial: https://www.bcb.gov.br/publicacoes/focus
- Padrão de URL do PDF: `https://www.bcb.gov.br/content/focus/focus/R<AAAAMMDD>.pdf`
  - Exemplo: `https://www.bcb.gov.br/content/focus/focus/R20260529.pdf`

## Convenções de Nomes de Arquivos

| Artefato | Padrão | Exemplo |
|---|---|---|
| PDF baixado | `focus_AAAA-MM-DD.pdf` | `focus_2026-05-29.pdf` |
| Texto extraído | `focus_AAAA-MM-DD.txt` | `focus_2026-05-29.txt` |
| Resumo executivo | `focus_AAAA-MM-DD.md` | `focus_2026-05-29.md` |

A data usada é sempre a **data de publicação** constante no próprio PDF, não a data de download.

## Estrutura de Pastas

```
Projeto_Boletim_Focus/
├── src/                  # código-fonte (downloader, extrator, resumidor)
├── tests/                # testes automatizados
├── data/                 # PDFs e textos extraídos
├── output/
│   └── focus/            # resumos executivos em Markdown
├── .github/
│   └── workflows/        # pipelines CI/CD e agendamento semanal
└── CLAUDE.md
```

## Regras de Negócio

### Nunca inventar números
Toda mediana, projeção ou estatística citada no resumo **deve estar presente no texto extraído do PDF**. É proibido estimar, interpolar ou inferir valores não escritos no boletim.

### Feriados na segunda-feira
O BCB publica o Focus toda segunda-feira. Quando segunda-feira é feriado nacional, a publicação ocorre na terça-feira. A lógica de download deve:
1. Tentar a segunda-feira da semana atual.
2. Se o PDF não existir, retroceder dia a dia (terça, quarta…) até encontrar o arquivo.
3. Registrar em log a data efetiva de publicação encontrada.

### Idempotência
Reexecutar o pipeline na mesma semana não deve duplicar arquivos nem sobrescrever resumos já gerados. Verificar existência antes de baixar/processar.

## Fluxo Geral

```
1. Descobrir a data de publicação da semana (segunda ou dia seguinte se feriado)
2. Montar a URL e baixar o PDF → data/focus_AAAA-MM-DD.pdf
3. Extrair o texto do PDF → data/focus_AAAA-MM-DD.txt
4. Gerar resumo executivo → output/focus/focus_AAAA-MM-DD.md
```
