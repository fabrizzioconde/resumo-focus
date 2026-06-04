# Roteiro semanal — Resumo do Boletim Focus

Execute os passos abaixo na ordem. Interrompa imediatamente se qualquer
condição de parada for atingida.

---

## Passo 1 — Localizar o texto mais recente

Procure todos os arquivos `data/focus_*.txt` e identifique o de nome
lexicograficamente maior (o mais recente, pois os nomes seguem o padrão
`focus_AAAA-MM-DD.txt`).

- Se não houver nenhum arquivo, **pare sem fazer nada** e registre:
  `Nenhum arquivo encontrado em data/. Execute primeiro o pipeline de download.`

---

## Passo 2 — Verificar o frescor do arquivo

Extraia a data do nome do arquivo (`focus_AAAA-MM-DD.txt`) e calcule a
diferença em dias em relação à data de hoje.

| Diferença | Ação |
|---|---|
| 0 a 3 dias | Prosseguir normalmente. |
| 4 a 7 dias | Prosseguir, mas incluir no cabeçalho do resumo a nota: `⚠️ Texto com X dias — verifique se há edição mais recente.` |
| Mais de 7 dias | **Parar.** Registre: `Arquivo com mais de 7 dias. Rode novamente o pipeline de download antes de gerar o resumo.` |

---

## Passo 3 — Sanity check do conteúdo

Leia o arquivo e verifique:

1. O texto tem **pelo menos 2000 caracteres**.
2. O texto contém as três palavras-chave obrigatórias: **IPCA**, **Selic** e **PIB**.

Se qualquer uma dessas condições falhar, **pare** e registre qual verificação
falhou (tamanho insuficiente ou palavra ausente). Isso indica que o layout do
boletim pode ter mudado e o resumo não deve ser gerado sem revisão humana.

---

## Passo 4 — Gerar o resumo executivo

Leia o texto completo e produza um documento Markdown com a estrutura abaixo.

**Regra absoluta: nenhum número, percentual ou projeção pode aparecer no
resumo que não esteja literalmente no texto do arquivo.** Em caso de dúvida,
omita o dado em vez de estimá-lo.

### Estrutura do documento a gerar

```
# Focus — DD/MM/AAAA
> Resumo gerado em AAAA-MM-DD.
[Nota de frescor, se aplicável — ver Passo 2]

## Medianas principais

Resumo executivo de **até 200 palavras** apresentando as medianas centrais do
boletim na seguinte ordem de prioridade: IPCA (ano corrente e próximo ano),
Selic (fim de ano), PIB (ano corrente), câmbio (fim de ano). Para cada
indicador, mencione se a mediana subiu, caiu ou ficou estável em relação à
edição anterior, caso essa informação esteja disponível no texto.

## Três principais revisões da semana

Liste as três revisões de expectativas mais relevantes da semana, no formato:

**1. [Indicador] — de X% para Y%**
Hipótese de motivo: [uma frase explicando o possível gatilho, derivada do
contexto do próprio texto ou de informações factuais contidas nele. Se o
texto não oferecer pista suficiente, escreva "Motivo não identificado no
texto."]

**2. ...** (idem)

**3. ...** (idem)
```

---

## Passo 5 — Salvar o resultado

Salve o documento gerado no Passo 4 em:

```
output/focus/focus_AAAA-MM-DD.md
```

onde `AAAA-MM-DD` é a data extraída do nome do arquivo `.txt` (data de
publicação do boletim, não a data de hoje).

Se já existir um arquivo com esse nome, **não sobrescreva** — registre:
`Resumo para esta data já existe em output/focus/. Nenhuma ação tomada.`

---

## Passo 6 — Enviar o resumo por e-mail

Envie o documento gerado no Passo 4 por e-mail para **fabrizzioconde@gmail.com**
usando a ferramenta Gmail disponível.

**Assunto:** `Focus BCB — DD/MM/AAAA` (onde `DD/MM/AAAA` é a data de publicação
do boletim, no formato brasileiro).

**Corpo:** cole o conteúdo completo do arquivo `.md` gerado, incluindo o
cabeçalho com a nota de frescor se ela estiver presente.

**Regras:**
- Envie apenas se o Passo 5 tiver sido concluído com sucesso (arquivo salvo
  ou já existente).
- Se o Passo 5 tiver sido pulado por arquivo já existente, não envie o e-mail
  novamente — o resumo dessa data já foi entregue anteriormente.
- Se o envio falhar, registre o erro mas não interrompa nem tente reenviar
  automaticamente.
