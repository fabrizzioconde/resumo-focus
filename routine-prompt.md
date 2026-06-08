# Roteiro semanal — Rascunho de e-mail do Boletim Focus

Execute os passos abaixo na ordem. Interrompa imediatamente se qualquer
condição de parada for atingida.

> **Arquitetura (importante).** A geração do resumo executivo é feita pelo
> **GitHub Actions** (workflow `focus-download.yml`), que baixa o PDF, extrai
> o texto, chama a API da Anthropic e **commita** o arquivo
> `output/focus/focus_AAAA-MM-DD.md` no branch `main` — porque só o Actions
> tem permissão de escrita confiável no repositório.
>
> **A sua tarefa nesta rotina NÃO é gerar nem commitar nada.** É apenas ler o
> resumo já versionado e criar um rascunho de e-mail com ele. Você roda ~45
> minutos depois do Actions, então o arquivo do dia já deve estar no repo.

---

## Passo 1 — Localizar o resumo mais recente

Procure todos os arquivos `output/focus/focus_*.md` e identifique o de nome
lexicograficamente maior (o mais recente, pois os nomes seguem o padrão
`focus_AAAA-MM-DD.md`). Ignore o arquivo `.gitkeep`.

- Se não houver nenhum arquivo `.md`, **pare sem fazer nada** e registre:
  `Nenhum resumo encontrado em output/focus/. O GitHub Actions ainda não gerou o arquivo desta semana.`

---

## Passo 2 — Verificar o frescor do arquivo

Extraia a data do nome do arquivo (`focus_AAAA-MM-DD.md`) e calcule a
diferença em dias em relação à data de hoje.

- **Mais de 7 dias:** **pare.** Registre:
  `Resumo mais recente tem mais de 7 dias (DD/MM/AAAA). O pipeline de download/geração pode ter falhado esta semana — verifique o GitHub Actions.`
- **Até 7 dias:** prossiga normalmente. (O próprio arquivo já traz, quando
  aplicável, a nota de frescor no cabeçalho — não é preciso adicioná-la.)

---

## Passo 3 — Evitar rascunho duplicado (idempotência)

Antes de criar o rascunho, verifique se já existe um rascunho no Gmail com o
assunto `Focus BCB — DD/MM/AAAA` (a data de publicação do arquivo, em formato
brasileiro).

- Se já existir um rascunho com esse assunto, **pare** e registre:
  `Rascunho para esta data já existe. Nenhuma ação tomada.`
- Caso contrário, prossiga para o Passo 4.

---

## Passo 4 — Criar o rascunho no Gmail

**Importante: a ferramenta Gmail disponível só permite CRIAR RASCUNHOS
(`create_draft`), não enviar e-mails diretamente.** Este passo gera um rascunho
pronto para revisão e envio manual.

Leia o conteúdo integral do arquivo `.md` localizado no Passo 1 e crie um
rascunho endereçado a **fabrizzioconde@gmail.com** com:

**Assunto:** `Focus BCB — DD/MM/AAAA` (data de publicação do boletim, no
formato brasileiro).

**Corpo:** o conteúdo completo do arquivo `.md`, exatamente como está
(incluindo o cabeçalho e a nota de frescor, se houver). **Não reescreva, não
resuma e não altere nenhum número** — o arquivo já é a versão final e
revisada. Apenas copie.

**Regras:**
- Não modifique o repositório: esta rotina não cria, edita nem commita
  arquivos. Sua única ação externa é criar o rascunho.
- Se a criação do rascunho falhar, registre o erro mas não interrompa nem
  tente novamente automaticamente. O resumo já está salvo no repositório
  (gerado pelo Actions), então nada se perde.

---

## Passo 5 — Relatar o resultado

Ao final, escreva um resumo claro do que foi feito: qual arquivo `.md` foi
usado, se o rascunho foi criado (ou por que algum passo foi pulado ou
interrompido).
