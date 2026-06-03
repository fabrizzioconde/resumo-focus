# Boletim Focus — Pipeline de Extração e Resumo

Pipeline que baixa automaticamente o Boletim Focus do Banco Central do Brasil, extrai o texto do PDF e, numa etapa de automação agendada, alimenta um agente que lê o texto extraído e gera um resumo executivo em Markdown — os scripts Python cuidam exclusivamente de baixar e extrair; nenhuma linha de código resume ou interpreta os dados.

## Estrutura

```
Projeto_Boletim_Focus/
├── src/
│   ├── baixar_focus.py    # baixa o PDF mais recente do BCB
│   └── extrair_texto.py   # extrai o texto do PDF para .txt
├── tests/
│   └── test_baixar_focus.py
├── data/                  # PDFs e .txt gerados (não versionados)
├── output/
│   └── focus/             # resumos executivos em Markdown
├── .github/
│   └── workflows/         # agendamento semanal do download
├── demo.py                # roda o pipeline completo localmente
├── requirements.txt
├── pytest.ini
└── CLAUDE.md              # briefing do projeto para o agente
```

## Como rodar localmente

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

Execute o pipeline completo (baixa o PDF e extrai o texto):

```bash
python demo.py
```

A flag `--abrir` abre o arquivo `.txt` gerado no navegador ao final:

```bash
python demo.py --abrir
```

## Testes

Rode todos os testes (incluindo os que fazem chamada de rede):

```bash
python -m pytest
```

Rode apenas os testes offline, pulando os que dependem de rede:

```bash
python -m pytest -m "not network"
```

Os testes marcados com `@pytest.mark.network` fazem download real do BCB e
são úteis para validar o pipeline de ponta a ponta, mas requerem conexão.

## Pipeline em duas etapas

O pipeline é dividido em duas etapas por uma razão prática: **o BCB bloqueia
requisições originadas de IPs de provedores de nuvem** (AWS, Azure, GitHub
Actions), mas aceita IPs residenciais e corporativos normais.

```
Etapa 1 — Download e extração (GitHub Actions, roda localmente ou em VPS)
  └─ baixa focus_AAAA-MM-DD.pdf → data/
  └─ extrai focus_AAAA-MM-DD.txt → data/

Etapa 2 — Resumo (automação separada, consome o .txt já pronto)
  └─ agente lê focus_AAAA-MM-DD.txt
  └─ gera focus_AAAA-MM-DD.md → output/focus/
```

A etapa 1 é agendada toda segunda-feira via `.github/workflows/`. Se o BCB
publicar na terça por conta de feriado, a lógica de download recua dia a dia
até encontrar o PDF. A etapa 2 consome o texto já salvo em `data/`, sem
nunca acessar o site do BCB diretamente.
