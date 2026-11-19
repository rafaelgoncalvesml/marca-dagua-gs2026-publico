# Dashboard de roadmap: plano de implementação

> **Para quem executa:** use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans, tarefa por tarefa. Os passos usam caixas de seleção (`- [ ]`).

**Objetivo:** um dashboard em HTML que mostra o projeto, a divisão entre Rafael e Charles e o roadmap de 05/11 a 19/11, com a tarefa diária de cada um e um botão que copia a tarefa do Charles para enviar a ele.

**Arquitetura:** site estático em `public/` (HTML, CSS e JS sem build, sem CDN), servido por um servidor Node curto que só escuta em `127.0.0.1`. Todo o conteúdo vem de `public/data/roadmap.json`. A lógica que dá para testar (escolha do dia, progresso, mensagem, validação dos dados) fica em módulos puros testados com `node --test`. O progresso das tarefas fica no `localStorage`.

**Stack:** Node 24 (já instalado), JavaScript ES modules, `node:test`. Nenhuma dependência npm.

**Spec:** `docs/superpowers/specs/2026-11-05-marca-dagua-design.md`

**Onde fica:** `C:\Users\Pichau\Desktop\FIAP\GS\GS 2\dashboard-roadmap\` (ferramenta da dupla, fora do repositório do portfólio, como decidido no spec).

## Restrições globais

- Sem CDN, sem fonte externa, sem biblioteca: funciona offline.
- O servidor escuta só em `127.0.0.1`, porta 5173 por padrão (variável `PORT`).
- CSP sem inline: nada de atributo `style=""` no HTML, nem `<script>` ou `<style>` embutidos. Valores dinâmicos entram por `element.style.setProperty` ou classes.
- Sem travessão (— e –) em nenhum texto da interface ou dos dados. Sem emoji. Ícones só em SVG próprio ou nenhum.
- Botões com raio de borda entre 4 e 8 px, nunca em formato de pílula. Alvos clicáveis com no mínimo 44 px de altura.
- Sem animação ao rolar, sem parallax, sem contador animado. Transição curta de foco e hover, e `prefers-reduced-motion` respeitado.
- Tema claro. Uma cor de destaque, que não seja roxo, violeta ou azul-índigo.
- `lang="pt-BR"`, `title`, `meta description` e favicon presentes.
- Nenhum dado numérico inventado: os números da tela vêm do `roadmap.json`.
- Texto em português correto, com acentos, sem "cara de IA" (passa pelo humanizer na Tarefa 6).

## Foco da revisão

Entradas que o spec não detalha e que costumam quebrar:

1. Caminho de requisição com `..` codificado (`/..%2fserver.js`) deve devolver 403, nunca o arquivo. Teste na Tarefa 1.
2. `localStorage` indisponível ou com JSON corrompido: o app abre com progresso zerado e não quebra. Teste na Tarefa 3.
3. Data de hoje fora de 05 a 19/11: mostrar o primeiro ou o último dia, com um aviso dizendo isso. Teste na Tarefa 4.
4. Copiar sem `navigator.clipboard`: mostrar o texto num campo já selecionado. Verificação no navegador na Tarefa 5.
5. Tela de 375 px de largura: o menu vira barra no topo e não há rolagem horizontal. Verificação no navegador na Tarefa 6.

## Estrutura de arquivos

```
dashboard-roadmap/
  package.json              type module, script "test" e "start"
  server.js                 servidor estático local (exporta createServer)
  README.md                 como abrir, em 4 linhas
  tests/
    server.test.js
    roadmap.test.js         integridade dos dados
    store.test.js
    logic.test.js           dates, stats e message
  public/
    index.html              casca: menu, área principal, favicon, meta
    favicon.svg
    css/style.css
    js/app.js               roteador por hash e renderização das telas
    js/dates.js             pickDay, hojeISO
    js/store.js             createStore
    js/stats.js             minutosPorPessoa, progresso, tarefasPorMateria
    js/message.js           mensagemDoDia
    data/roadmap.json       todo o conteúdo
```

---

### Tarefa 1: Servidor local seguro e casca da página

**Arquivos:**
- Criar: `package.json`, `server.js`, `tests/server.test.js`, `public/index.html`, `public/favicon.svg`, `public/css/style.css` (vazio por enquanto), `public/js/app.js` (vazio por enquanto), `public/data/roadmap.json` (`{}` por enquanto)

**Interfaces:**
- Produz: `createServer(rootDir: string): http.Server` exportado de `server.js`. Quando executado direto, escuta em `127.0.0.1:${PORT || 5173}`.

- [ ] **Passo 1: criar `package.json`**

```json
{
  "name": "dashboard-roadmap",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node server.js",
    "test": "node --test tests/"
  }
}
```

- [ ] **Passo 2: escrever o teste que falha**

`tests/server.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from '../server.js';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'public');

function pedir(porta, caminho, metodo = 'GET') {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port: porta, path: caminho, method: metodo }, (res) => {
      let corpo = '';
      res.on('data', (c) => (corpo += c));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, corpo }));
    });
    req.on('error', reject);
    req.end();
  });
}

async function comServidor(fn) {
  const server = createServer(root);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  try {
    await fn(server.address().port);
  } finally {
    await new Promise((r) => server.close(r));
  }
}

test('serve a página inicial com cabeçalhos de segurança', () =>
  comServidor(async (porta) => {
    const r = await pedir(porta, '/');
    assert.equal(r.status, 200);
    assert.match(r.headers['content-type'], /text\/html/);
    assert.equal(r.headers['x-content-type-options'], 'nosniff');
    assert.match(r.headers['content-security-policy'], /default-src 'self'/);
  }));

test('serve o JSON de dados', () =>
  comServidor(async (porta) => {
    const r = await pedir(porta, '/data/roadmap.json');
    assert.equal(r.status, 200);
    assert.match(r.headers['content-type'], /application\/json/);
  }));

test('barra caminho com .. codificado', () =>
  comServidor(async (porta) => {
    for (const caminho of ['/..%2fserver.js', '/%2e%2e%2fpackage.json', '/..%5cserver.js']) {
      const r = await pedir(porta, caminho);
      assert.ok([400, 403, 404].includes(r.status), `${caminho} devolveu ${r.status}`);
      assert.doesNotMatch(r.corpo, /createServer/);
    }
  }));

test('recusa métodos diferentes de GET e HEAD', () =>
  comServidor(async (porta) => {
    const r = await pedir(porta, '/', 'POST');
    assert.equal(r.status, 405);
  }));

test('arquivo inexistente devolve 404', () =>
  comServidor(async (porta) => {
    const r = await pedir(porta, '/nao-existe.js');
    assert.equal(r.status, 404);
  }));
```

- [ ] **Passo 3: rodar e ver falhar**

Run: `node --test tests/server.test.js`
Expected: FAIL com `Cannot find module '../server.js'` (ou `ERR_MODULE_NOT_FOUND`).

- [ ] **Passo 4: implementar `server.js`**

```js
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const TIPOS = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
};

const CABECALHOS = {
  'X-Content-Type-Options': 'nosniff',
  'Content-Security-Policy':
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'",
  'Referrer-Policy': 'no-referrer',
  'Cache-Control': 'no-store',
};

export function createServer(rootDir) {
  const base = path.resolve(rootDir);

  return http.createServer(async (req, res) => {
    const responder = (codigo, corpo, tipo = 'text/plain; charset=utf-8') => {
      res.writeHead(codigo, { ...CABECALHOS, 'Content-Type': tipo });
      res.end(req.method === 'HEAD' ? undefined : corpo);
    };

    if (req.method !== 'GET' && req.method !== 'HEAD') return responder(405, 'método não permitido');

    let rel;
    try {
      rel = decodeURIComponent(new URL(req.url, 'http://local').pathname);
    } catch {
      return responder(400, 'requisição inválida');
    }
    if (rel.includes('\0') || rel.includes('\\')) return responder(400, 'requisição inválida');
    if (rel.endsWith('/')) rel += 'index.html';

    const arquivo = path.resolve(base, '.' + rel);
    if (arquivo !== base && !arquivo.startsWith(base + path.sep)) return responder(403, 'acesso negado');

    try {
      const conteudo = await readFile(arquivo);
      const tipo = TIPOS[path.extname(arquivo)] ?? 'application/octet-stream';
      responder(200, conteudo, tipo);
    } catch {
      responder(404, 'não encontrado');
    }
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const porta = Number(process.env.PORT) || 5173;
  const raiz = path.join(path.dirname(fileURLToPath(import.meta.url)), 'public');
  createServer(raiz).listen(porta, '127.0.0.1', () => {
    console.log(`Dashboard em http://localhost:${porta}`);
  });
}
```

- [ ] **Passo 5: criar a casca mínima para o teste de `/` passar**

`public/index.html`:

```html
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Marca d'Água · Roadmap da GS2</title>
  <meta name="description" content="Roadmap diário da Global Solution 2026.2 para Rafael e Charles, de 05/11 a 19/11.">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <div id="app"></div>
  <script type="module" src="js/app.js"></script>
</body>
</html>
```

`public/favicon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#1f5f5b"/><path d="M5 21c3-3 5-3 8 0s5 3 8 0 4-3 6-1" fill="none" stroke="#f4efe6" stroke-width="2.4" stroke-linecap="round"/><path d="M5 14c3-3 5-3 8 0s5 3 8 0 4-3 6-1" fill="none" stroke="#f4efe6" stroke-width="2.4" stroke-linecap="round" opacity=".55"/></svg>
```

Criar `public/css/style.css` e `public/js/app.js` vazios e `public/data/roadmap.json` com `{}`.

- [ ] **Passo 6: rodar e ver passar**

Run: `node --test tests/server.test.js`
Expected: PASS nos 5 testes.

- [ ] **Passo 7: conferir manualmente**

Run: `node server.js` e abrir `http://localhost:5173`. Esperado: página em branco com título "Marca d'Água · Roadmap da GS2" e o ícone de onda na aba. Parar com Ctrl+C.

---

### Tarefa 2: Dados do roadmap e testes de integridade

**Arquivos:**
- Modificar: `public/data/roadmap.json`
- Criar: `tests/roadmap.test.js`

**Interfaces:**
- Produz o formato abaixo, que as Tarefas 3 a 5 consomem.

```
{
  "projeto": { "nome", "subtitulo", "resumo": [string], "fluxo": [string], "inicio": "2026-11-05", "fim": "2026-11-19", "entrega": "19/11/2026, 23h55" },
  "membros": [ { "id": "rafael"|"charles", "nome", "rm", "papel", "materias": [materiaId] } ],
  "materias": [ { "id", "nome", "dono": "rafael"|"charles", "entregavel": string, "criterios": [ { "item", "pontos" } ], "formato": string } ],
  "fases": [ { "nome", "de": "AAAA-MM-DD", "ate": "AAAA-MM-DD", "foco": string } ],
  "dias": [ { "data": "AAAA-MM-DD", "tipo": "normal"|"execucao"|"reserva", "fase": string, "meta": string,
              "tarefas": [ { "id": "d05-r1", "pessoa": "rafael"|"charles", "materia": materiaId, "minutos": number,
                             "titulo": string, "como": string, "claude": string } ] } ],
  "riscos": [ { "risco", "tratamento" } ],
  "pendencias": [ { "item", "quem", "ate" } ]
}
```

IDs de matéria válidos: `aicss`, `python`, `cyber`, `dados`, `ml`, `rna`, `stat`, `aws`, `aic`, `geral`.

- [ ] **Passo 1: escrever o teste de integridade (falha, o JSON ainda está vazio)**

`tests/roadmap.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const R = JSON.parse(readFileSync(new URL('../public/data/roadmap.json', import.meta.url), 'utf8'));
const MATERIAS = ['aicss', 'python', 'cyber', 'dados', 'ml', 'rna', 'stat', 'aws', 'aic', 'geral'];
const PESSOAS = ['rafael', 'charles'];
const EXECUCAO = ['2026-11-10', '2026-11-14', '2026-11-17'];

const tarefas = () => R.dias.flatMap((d) => d.tarefas.map((t) => ({ ...t, data: d.data, tipo: d.tipo })));
const minutosDia = (dia, pessoa) => dia.tarefas.filter((t) => t.pessoa === pessoa).reduce((s, t) => s + t.minutos, 0);

test('15 dias seguidos, de 05/11 a 19/11', () => {
  assert.equal(R.dias.length, 15);
  assert.equal(R.dias[0].data, '2026-11-05');
  assert.equal(R.dias[14].data, '2026-11-19');
  for (let i = 1; i < R.dias.length; i++) {
    const anterior = new Date(R.dias[i - 1].data + 'T12:00:00Z');
    const atual = new Date(R.dias[i].data + 'T12:00:00Z');
    assert.equal((atual - anterior) / 86400000, 1, `buraco antes de ${R.dias[i].data}`);
  }
});

test('os três dias de execução são 10, 14 e 17/11 e 19/11 é reserva', () => {
  const exec = R.dias.filter((d) => d.tipo === 'execucao').map((d) => d.data);
  assert.deepEqual(exec, EXECUCAO);
  assert.equal(R.dias.find((d) => d.data === '2026-11-19').tipo, 'reserva');
});

test('toda tarefa tem pessoa, matéria, minutos e textos preenchidos', () => {
  for (const t of tarefas()) {
    assert.ok(PESSOAS.includes(t.pessoa), `${t.id}: pessoa`);
    assert.ok(MATERIAS.includes(t.materia), `${t.id}: matéria ${t.materia}`);
    assert.ok(Number.isInteger(t.minutos) && t.minutos > 0, `${t.id}: minutos`);
    for (const campo of ['titulo', 'como', 'claude']) {
      assert.ok(typeof t[campo] === 'string' && t[campo].trim().length > 5, `${t.id}: ${campo}`);
    }
  }
});

test('ids de tarefa são únicos', () => {
  const ids = tarefas().map((t) => t.id);
  assert.equal(new Set(ids).size, ids.length);
});

test('minutos por pessoa e por dia respeitam o orçamento', () => {
  for (const dia of R.dias) {
    for (const p of PESSOAS) {
      const m = minutosDia(dia, p);
      const teto = dia.tipo === 'execucao' ? 95 : dia.tipo === 'reserva' ? 20 : 35;
      assert.ok(m >= 15 && m <= teto, `${dia.data} ${p}: ${m} min (teto ${teto})`);
    }
  }
});

test('total por pessoa fica entre 9 e 12 horas e os dois são parecidos', () => {
  const total = (p) => tarefas().filter((t) => t.pessoa === p).reduce((s, t) => s + t.minutos, 0);
  const r = total('rafael');
  const c = total('charles');
  assert.ok(r >= 540 && r <= 720, `rafael ${r}`);
  assert.ok(c >= 540 && c <= 720, `charles ${c}`);
  assert.ok(Math.abs(r - c) <= 45, `diferença ${Math.abs(r - c)}`);
});

test('cada matéria tem dono e tarefas do dono, e os donos batem com os membros', () => {
  for (const m of R.materias.filter((x) => x.id !== 'geral')) {
    const dono = R.membros.find((p) => p.materias.includes(m.id));
    assert.ok(dono, `${m.id} sem membro responsável`);
    assert.equal(dono.id, m.dono, `${m.id}: dono inconsistente`);
    const dele = tarefas().filter((t) => t.materia === m.id && t.pessoa === m.dono);
    // AWS tem só 2 tarefas porque o enunciado ainda não saiu; sobe quando sair
    const minimo = m.id === 'aws' ? 2 : 3;
    assert.ok(dele.length >= minimo, `${m.id}: só ${dele.length} tarefas do dono`);
  }
});

test('critérios de cada matéria somam 10 pontos', () => {
  for (const m of R.materias.filter((x) => x.id !== 'geral')) {
    const soma = m.criterios.reduce((s, c) => s + c.pontos, 0);
    assert.ok(Math.abs(soma - 10) < 0.001, `${m.id}: ${soma}`);
  }
});

test('as fases cobrem todos os dias e os dias apontam para uma fase existente', () => {
  const nomes = R.fases.map((f) => f.nome);
  for (const dia of R.dias) {
    assert.ok(nomes.includes(dia.fase), `${dia.data}: fase ${dia.fase}`);
    const fase = R.fases.find((f) => f.nome === dia.fase);
    assert.ok(dia.data >= fase.de && dia.data <= fase.ate, `${dia.data} fora de ${fase.nome}`);
  }
});

test('nenhum texto tem travessão nem emoji', () => {
  const texto = JSON.stringify(R);
  assert.doesNotMatch(texto, /[\u2013\u2014]/, 'travessão encontrado');
  assert.doesNotMatch(texto, /\p{Extended_Pictographic}/u, 'emoji encontrado');
});
```

- [ ] **Passo 2: rodar e ver falhar**

Run: `node --test tests/roadmap.test.js`
Expected: FAIL (`R.dias` indefinido).

- [ ] **Passo 3: escrever `public/data/roadmap.json` a partir das tabelas abaixo**

Fonte única da verdade para as tarefas. Cada linha vira um objeto em `dias[].tarefas[]`. O id segue `dDD-rN` (Rafael) e `dDD-cN` (Charles), com N na ordem da linha. Os campos `como` (passo a passo curto, 1 a 3 frases, com o comando quando houver) e `claude` (o que o Claude entrega antes da tarefa) são escritos na execução e partem das colunas "Tarefa" e "Claude entrega" abaixo. Textos em português com acento, sem travessão, em tom de instrução direta.

Legenda de matérias: AICSS `aicss`, Python `python`, Cyber `cyber`, Data Science `dados`, ML `ml`, Redes Neurais `rna`, Statistical `stat`, AWS `aws`, AI Challenges `aic`, geral `geral`.

**Quinta, 05/11 · Fase 0 · normal** · meta: ambiente pronto e pendências externas disparadas

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | geral | 10 | Instalar o Python 3.12 (`winget install Python.Python.3.12`) e conferir com `py --version` | Comando e checagem |
| Rafael | rna | 10 | Enviar ao professor de Redes Neurais o pedido de validação da base INMET Porto Alegre | Texto do e-mail pronto |
| Rafael | geral | 10 | Criar conta no Wokwi e responder qual conta do GitHub vai ficar com o repositório | Link e passo a passo |
| Charles | geral | 15 | Anotar 3 ideias da live de 04/11, com o minuto da gravação | Perguntas para guiar a anotação |
| Charles | geral | 15 | Instalar o Python 3.12 e o Git e conferir com `py --version` e `git --version` | Comandos |

**Sexta, 06/11 · Fase 0 · normal** · meta: circuito montado, API no ar, ferramentas de banco abertas

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | aicss | 15 | Montar o circuito no Wokwi colando o `diagram.json` e rodar sem erro | `diagram.json` e `libraries.txt` |
| Rafael | geral | 10 | Testar o download do CSV do nível do Guaíba no HidroWeb (estação 87450004) e anotar se deu certo | Passo a passo do site |
| Rafael | geral | 5 | Abrir o Kanban e conferir se os cartões das matérias estão nas colunas certas | Quadro criado com os cartões |
| Charles | python | 15 | Criar o ambiente virtual, instalar as dependências e abrir `/health` da API | `requirements.txt` e `main.py` mínimo |
| Charles | dados | 15 | Instalar Oracle Data Modeler, SQL Developer, MongoDB Compass e Shell, e abrir cada um | Links e lista de conferência |

**Sábado, 07/11 · Fase 1 · normal** · meta: primeiro alerta no Wokwi e API gravando CSV

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | geral | 10 | Decidir plano A ou B do alvo, com o resultado do HidroWeb | Critérios de decisão |
| Rafael | aicss | 20 | Rodar o sketch v1 no Wokwi e salvar o print do comportamento 1 (tudo OK) | `sketch.ino` v1 |
| Charles | python | 30 | Rodar a API v1, enviar 3 cenários de teste e conferir o CSV gerado | `main.py`, script dos 3 cenários |

**Domingo, 08/11 · Fase 1 · normal** · meta: três comportamentos do nó e base INMET baixada

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | aicss | 30 | Provocar os comportamentos 2 e 3 (chuva forte e nível crítico), salvar prints e o JSON da saída serial | Roteiro de cenários |
| Charles | stat | 30 | Rodar o script que baixa o INMET e conferir o CSV (linhas, colunas, falhas) | Script de download e proposta de variáveis |

**Segunda, 09/11 · Fase 1 · normal** · meta: EDA do ML feita e modelo lógico no Data Modeler

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | ml | 30 | Rodar o notebook de EDA e pré-processamento no Colab e conferir os gráficos | Notebook de EDA |
| Charles | dados | 30 | Recriar o modelo lógico (6 tabelas) no Oracle Data Modeler | Modelo em texto e diagrama |

**Terça, 10/11 · Fase 1 · execução (90 min)** · meta: nó conversando com a API; AICSS e Python prontos para enviar

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | aicss | 60 | Ligar o túnel até a API, rodar o Wokwi enviando JSON, testar a fila offline e tirar os prints | `sketch.ino` v2 e instruções do túnel |
| Rafael | aicss | 30 | Conferir e fechar o PDF do AICSS (capa, arquitetura, evidências, ODS) | PDF rascunho |
| Charles | python | 40 | Rodar o pytest, conferir o indicador e fechar o PDF de Python | Testes e PDF rascunho |
| Charles | dados | 50 | Gerar o modelo relacional, exportar o `.dmd` e o DDL e conferir a 3FN | DDL e texto sobre a 3FN |

**Quarta, 11/11 · Fase 2 · normal** · meta: modelos de ML treinados; estatística 02 e 03 rodadas

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | ml | 30 | Rodar baseline, 2 modelos e o tuning, e anotar as métricas | Notebook de modelagem |
| Charles | stat | 30 | Rodar as questões 02 e 03 (probabilidades na normal e testes de hipótese a 6% com n=20 e 9% com n=25) | Script `.py` |

**Quinta, 12/11 · Fase 2 · normal** · meta: modelo final escolhido; ameaças priorizadas; regressões rodadas

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | ml | 15 | Ler a importância das variáveis, ajustar o limiar e escolher o modelo final | Texto de interpretação |
| Rafael | cyber | 15 | Revisar o inventário de ameaças e escolher as 3 prioridades | Inventário de ameaças |
| Charles | stat | 30 | Rodar as questões 04 e 05 (regressão simples e múltipla, com gráficos) | Script `.py` |

**Sexta, 13/11 · Fase 2 · normal** · meta: rede neural treinada; Oracle executado com prints

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | rna | 30 | Rodar o notebook completo (MLP, LSTM ou GRU, early stopping) | Notebook de Redes Neurais |
| Charles | dados | 30 | Rodar o `oracle.sql` no SQL Developer e tirar prints de criação, inserts e SELECT | `oracle.sql` |

**Sábado, 14/11 · Fase 2 · execução (90 min)** · meta: Mongo e demonstração cruzada feitos; proteção da API provada

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | rna | 40 | Rodar a regularização, a comparação de configurações e a demo com dados não vistos | Células de refinamento e demo |
| Rafael | cyber | 30 | Aplicar a proteção na API (chave e limite) e tirar os prints de 401 e 429 | Alteração na API e roteiro |
| Rafael | cyber | 20 | Revisar o texto de LGPD do cadastro de moradores | Rascunho de LGPD |
| Charles | dados | 40 | Criar banco e coleção no Mongo, inserir 10 documentos e rodar 3 consultas com prints | `mongodb.txt` |
| Charles | dados | 30 | Rodar a demonstração cruzada Oracle e Mongo e montar o ZIP | Consultas e PDF |
| Charles | stat | 20 | Rodar a questão 06 (regressão logística e matriz de confusão) | Script `.py` |

**Domingo, 15/11 · Fase 3 · normal** · meta: slides do ML prontos; relatório estatístico fechado; UML exportada

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | ml | 30 | Revisar os slides do ML e conferir o notebook final | Slides |
| Charles | stat | 20 | Fechar o relatório estatístico em PDF e conferir os insights | Texto do relatório |
| Charles | aic | 10 | Exportar os diagramas UML (componentes e sequência) em PNG | Código dos diagramas |

**Segunda, 16/11 · Fase 3 · normal** · meta: Redes Neurais e Cyber fechados; ingestão na AWS montada

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | rna | 15 | Limpar o notebook e conferir a documentação de decisões e limitações | Texto de documentação |
| Rafael | cyber | 15 | Fechar o relatório de Cyber (ameaças, controles, prova de proteção, LGPD) | PDF do relatório |
| Charles | aws | 30 | Montar a ingestão serverless e testar uma notificação (provisório até sair o enunciado) | Funções e roteiro |

**Terça, 17/11 · Fase 4 · execução (90 min)** · meta: todos os vídeos gravados; AWS com evidência; ZIP de dados conferido

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | ml | 20 | Gravar o vídeo do ML (até 5 min) | Roteiro |
| Rafael | rna | 15 | Gravar a demonstração da rede neural | Roteiro |
| Rafael | aic | 40 | Gravar o pitch de até 7 min com rosto e publicar como não listado | Roteiro minutado e lista de telas |
| Rafael | aic | 15 | Conferir nomes e RMs na tela, o link e o acesso ao vídeo | Lista de conferência |
| Charles | aws | 40 | Tirar prints do monitoramento e da notificação | Roteiro de evidências |
| Charles | dados | 20 | Conferir o ZIP final (PDF, `oracle.sql`, `mongodb.txt`, `.dmd` e pasta) | Lista de conferência |
| Charles | aic | 30 | Fechar o Kanban final e mandar a UML e o quadro ao Rafael para o vídeo | Quadro atualizado |

**Quarta, 18/11 · Fase 4 · normal** · meta: tudo enviado no Portal

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | geral | 30 | Enviar AICSS, Cyber, ML e Redes Neurais no Portal e guardar os comprovantes | Lista por entrega |
| Charles | geral | 30 | Enviar Python, Data Science, Statistical e AWS no Portal e guardar os comprovantes | Lista por entrega |

**Quinta, 19/11 · reserva · prazo 23h55** · meta: link do vídeo enviado e nada faltando

| Quem | Mat. | Min | Tarefa | Claude entrega |
|---|---|---|---|---|
| Rafael | aic | 15 | Enviar o link do vídeo no Portal e conferir se abre sem login | Lista de conferência |
| Charles | geral | 15 | Conferir os comprovantes de todas as entregas e avisar se algo faltar | Lista de conferência |

Os demais blocos do JSON:

- `projeto`: nome "Marca d'Água", subtítulo "Alerta de alagamento para quem mora em área de risco em Porto Alegre", `resumo` com 3 parágrafos curtos tirados das seções 1 e 2 do spec, `fluxo` com as 8 etapas do diagrama do spec.
- `membros`: Rafael (RM 569461, papel "hardware, modelos e narração", matérias `aicss`, `cyber`, `ml`, `rna`, `aic`) e Charles (RM 571908, papel "backend, dados e nuvem", matérias `python`, `dados`, `stat`, `aws`). O dono de `aic` é Rafael, que narra o vídeo; Charles faz a UML e o Kanban dentro do AI Challenges (descrito em `papel`).
- `materias`: as 9 do spec mais `geral`, com `entregavel`, `formato` e `criterios` copiados dos enunciados (AICSS 1+3+3+2+1, Python 1+2+2+2+2+1, Redes Neurais 1+1+2+1,5+1,5+1+1+1, ML 3+2+2+1,5+1+0,5, Data Science 1+2+2+1,5+2+1,5, AIC 1,5+2,5+3+1,5+1,5; Cyber, Statistical (itens 02 a 07 do enunciado, com os pesos 1+1+2+2+2+2) e AWS ainda sem critérios publicados: usar `[{ "item": "Critérios a confirmar no Portal", "pontos": 10 }]`).
- `fases`: as 5 do spec (Fundação 05 a 06, Dados e dispositivo 07 a 10, Modelos e armazenamento 11 a 14, Integração 15 a 16, Fechamento 17 a 19). A fase de cada dia é a que o contém; o dia 19 usa "Fechamento".
- `riscos`: a tabela da seção 7 do spec.
- `pendencias`: as 5 da seção 12 do spec, com `quem` e `ate` (conta GitHub: Rafael, 05/11; enunciado AWS: Charles, 12/11; validação da base: Rafael, 07/11; live: Charles, 08/11; cota oficial: Rafael, 07/11).

- [ ] **Passo 4: rodar e ver passar**

Run: `node --test tests/roadmap.test.js`
Expected: PASS nos 10 testes. Se o teste de orçamento falhar, corrigir o JSON (as tabelas acima já fecham 30, 90 e 15 minutos por pessoa por dia, com 615 minutos por pessoa no total).

---

### Tarefa 3: Armazenamento do progresso

**Arquivos:**
- Criar: `public/js/store.js`, `tests/store.test.js`

**Interfaces:**
- Produz: `createStore(storage?: Storage, chave?: string)` devolvendo `{ isDone(id): boolean, toggle(id): boolean, count(): number, reset(): void }`. `toggle` devolve o novo estado. Sem `storage` utilizável, usa memória.

- [ ] **Passo 1: escrever o teste que falha**

`tests/store.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../public/js/store.js';

function fakeStorage(inicial = {}) {
  const dados = { ...inicial };
  return {
    getItem: (k) => (k in dados ? dados[k] : null),
    setItem: (k, v) => { dados[k] = String(v); },
    removeItem: (k) => { delete dados[k]; },
    dados,
  };
}

test('marca e desmarca uma tarefa', () => {
  const s = createStore(fakeStorage());
  assert.equal(s.isDone('d05-r1'), false);
  assert.equal(s.toggle('d05-r1'), true);
  assert.equal(s.isDone('d05-r1'), true);
  assert.equal(s.toggle('d05-r1'), false);
  assert.equal(s.count(), 0);
});

test('persiste entre instâncias', () => {
  const st = fakeStorage();
  createStore(st).toggle('d06-c2');
  assert.equal(createStore(st).isDone('d06-c2'), true);
});

test('JSON corrompido no storage começa do zero sem lançar erro', () => {
  const st = fakeStorage({ 'marca-dagua-roadmap-v1': '{quebrado' });
  const s = createStore(st);
  assert.equal(s.count(), 0);
  assert.equal(s.toggle('d05-r1'), true);
});

test('valor com formato errado no storage é ignorado', () => {
  const st = fakeStorage({ 'marca-dagua-roadmap-v1': '["d05-r1"]' });
  assert.equal(createStore(st).count(), 0);
});

test('storage que lança erro ao gravar continua funcionando na memória', () => {
  const ruim = {
    getItem: () => { throw new Error('bloqueado'); },
    setItem: () => { throw new Error('bloqueado'); },
    removeItem: () => {},
  };
  const s = createStore(ruim);
  assert.equal(s.toggle('d05-r1'), true);
  assert.equal(s.isDone('d05-r1'), true);
});

test('sem storage usa só memória', () => {
  const s = createStore(undefined);
  s.toggle('x');
  assert.equal(s.count(), 1);
  s.reset();
  assert.equal(s.count(), 0);
});
```

- [ ] **Passo 2: rodar e ver falhar**

Run: `node --test tests/store.test.js`
Expected: FAIL com módulo não encontrado.

- [ ] **Passo 3: implementar `public/js/store.js`**

```js
const CHAVE = 'marca-dagua-roadmap-v1';

function ler(storage, chave) {
  try {
    const bruto = storage?.getItem(chave);
    if (!bruto) return {};
    const valor = JSON.parse(bruto);
    if (valor === null || typeof valor !== 'object' || Array.isArray(valor)) return {};
    return valor;
  } catch {
    return {};
  }
}

export function createStore(storage, chave = CHAVE) {
  let feitos = ler(storage, chave);

  const gravar = () => {
    try {
      storage?.setItem(chave, JSON.stringify(feitos));
    } catch {
      // sem espaço ou bloqueado: o progresso vale só nesta sessão
    }
  };

  return {
    isDone: (id) => feitos[id] === true,
    toggle(id) {
      if (feitos[id]) delete feitos[id];
      else feitos[id] = true;
      gravar();
      return feitos[id] === true;
    },
    count: () => Object.keys(feitos).length,
    reset() {
      feitos = {};
      try {
        storage?.removeItem(chave);
      } catch {
        // ignora
      }
    },
  };
}
```

- [ ] **Passo 4: rodar e ver passar**

Run: `node --test tests/store.test.js`
Expected: PASS nos 6 testes.

---

### Tarefa 4: Lógica de datas, estatísticas e mensagem

**Arquivos:**
- Criar: `public/js/dates.js`, `public/js/stats.js`, `public/js/message.js`, `tests/logic.test.js`

**Interfaces:**
- Consome: formato do `roadmap.json` (Tarefa 2) e `createStore` (Tarefa 3).
- Produz:
  - `hojeISO(agora?: Date): string` no formato `AAAA-MM-DD` pela data local.
  - `pickDay(iso: string, dias): { dia, estado: 'antes' | 'durante' | 'depois' }`.
  - `minutosPorPessoa(dias): { rafael: number, charles: number }`.
  - `progresso(dias, store, pessoa?): { feitas: number, total: number, pct: number }`.
  - `tarefasPorMateria(dias, materiaId): Array<tarefa & { data: string }>`.
  - `mensagemDoDia(dia, pessoaId, membros): string`.

- [ ] **Passo 1: escrever o teste que falha**

`tests/logic.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { hojeISO, pickDay } from '../public/js/dates.js';
import { minutosPorPessoa, progresso, tarefasPorMateria } from '../public/js/stats.js';
import { mensagemDoDia } from '../public/js/message.js';
import { createStore } from '../public/js/store.js';

const dias = [
  { data: '2026-11-05', tipo: 'normal', meta: 'ambiente pronto', tarefas: [
    { id: 'd05-r1', pessoa: 'rafael', materia: 'geral', minutos: 10, titulo: 'Instalar o Python', como: 'Rode o winget', claude: 'Comando' },
    { id: 'd05-c1', pessoa: 'charles', materia: 'geral', minutos: 15, titulo: 'Anotar ideias da live', como: 'Veja a gravação', claude: 'Perguntas' },
    { id: 'd05-c2', pessoa: 'charles', materia: 'python', minutos: 15, titulo: 'Instalar Git', como: 'Rode o winget', claude: 'Comandos' },
  ] },
  { data: '2026-11-06', tipo: 'normal', meta: 'API no ar', tarefas: [
    { id: 'd06-r1', pessoa: 'rafael', materia: 'aicss', minutos: 15, titulo: 'Montar o circuito', como: 'Cole o JSON', claude: 'diagram.json' },
  ] },
];
const membros = [{ id: 'rafael', nome: 'Rafael' }, { id: 'charles', nome: 'Charles' }];

test('hojeISO usa a data local', () => {
  assert.equal(hojeISO(new Date(2026, 10, 5, 23, 59)), '2026-11-05');
  assert.equal(hojeISO(new Date(2026, 10, 9, 0, 1)), '2026-11-09');
});

test('pickDay devolve o dia de hoje quando está no intervalo', () => {
  const r = pickDay('2026-11-06', dias);
  assert.equal(r.estado, 'durante');
  assert.equal(r.dia.data, '2026-11-06');
});

test('pickDay antes do início devolve o primeiro dia com estado antes', () => {
  const r = pickDay('2026-11-01', dias);
  assert.equal(r.estado, 'antes');
  assert.equal(r.dia.data, '2026-11-05');
});

test('pickDay depois do fim devolve o último dia com estado depois', () => {
  const r = pickDay('2026-12-01', dias);
  assert.equal(r.estado, 'depois');
  assert.equal(r.dia.data, '2026-11-06');
});

test('minutosPorPessoa soma por pessoa', () => {
  assert.deepEqual(minutosPorPessoa(dias), { rafael: 25, charles: 30 });
});

test('progresso conta tarefas feitas por pessoa e no total', () => {
  const s = createStore(undefined);
  s.toggle('d05-c1');
  s.toggle('d06-r1');
  assert.deepEqual(progresso(dias, s, 'charles'), { feitas: 1, total: 2, pct: 50 });
  assert.deepEqual(progresso(dias, s), { feitas: 2, total: 4, pct: 50 });
});

test('progresso sem tarefas dá 0 e não divide por zero', () => {
  assert.deepEqual(progresso([], createStore(undefined)), { feitas: 0, total: 0, pct: 0 });
});

test('tarefasPorMateria devolve as tarefas com a data', () => {
  const r = tarefasPorMateria(dias, 'aicss');
  assert.equal(r.length, 1);
  assert.equal(r[0].data, '2026-11-06');
});

test('mensagemDoDia monta o texto do dia para uma pessoa', () => {
  const texto = mensagemDoDia(dias[0], 'charles', membros);
  assert.match(texto, /^Charles, suas tarefas de quinta-feira, 05\/11 \(30 min\):/);
  assert.match(texto, /1\. \[geral\] Anotar ideias da live \(15 min\)/);
  assert.match(texto, /Como: Veja a gravação/);
  assert.match(texto, /Eu preparo: Perguntas/);
  assert.match(texto, /2\. \[python\] Instalar Git \(15 min\)/);
  assert.match(texto, /Meta do dia: ambiente pronto/);
});

test('mensagemDoDia para quem não tem tarefa no dia avisa isso', () => {
  const texto = mensagemDoDia({ data: '2026-11-07', meta: 'x', tarefas: [] }, 'charles', membros);
  assert.match(texto, /Sem tarefas neste dia/);
});
```

- [ ] **Passo 2: rodar e ver falhar**

Run: `node --test tests/logic.test.js`
Expected: FAIL com módulo não encontrado.

- [ ] **Passo 3: implementar os três módulos**

`public/js/dates.js`:

```js
export function hojeISO(agora = new Date()) {
  const m = String(agora.getMonth() + 1).padStart(2, '0');
  const d = String(agora.getDate()).padStart(2, '0');
  return `${agora.getFullYear()}-${m}-${d}`;
}

export function pickDay(iso, dias) {
  const primeiro = dias[0];
  const ultimo = dias[dias.length - 1];
  if (iso < primeiro.data) return { dia: primeiro, estado: 'antes' };
  if (iso > ultimo.data) return { dia: ultimo, estado: 'depois' };
  return { dia: dias.find((d) => d.data === iso) ?? primeiro, estado: 'durante' };
}
```

`public/js/stats.js`:

```js
export function minutosPorPessoa(dias) {
  const total = { rafael: 0, charles: 0 };
  for (const dia of dias) {
    for (const t of dia.tarefas) total[t.pessoa] += t.minutos;
  }
  return total;
}

export function progresso(dias, store, pessoa) {
  const todas = dias.flatMap((d) => d.tarefas).filter((t) => !pessoa || t.pessoa === pessoa);
  const feitas = todas.filter((t) => store.isDone(t.id)).length;
  const total = todas.length;
  return { feitas, total, pct: total === 0 ? 0 : Math.round((feitas / total) * 100) };
}

export function tarefasPorMateria(dias, materiaId) {
  return dias.flatMap((d) => d.tarefas.filter((t) => t.materia === materiaId).map((t) => ({ ...t, data: d.data })));
}
```

`public/js/message.js`:

```js
function diaDaSemana(iso) {
  return new Date(iso + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'long' });
}

function diaMes(iso) {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}

export function mensagemDoDia(dia, pessoaId, membros) {
  const pessoa = membros.find((m) => m.id === pessoaId);
  const minhas = dia.tarefas.filter((t) => t.pessoa === pessoaId);
  const cabecalho = `${pessoa.nome}, suas tarefas de ${diaDaSemana(dia.data)}, ${diaMes(dia.data)}`;

  if (minhas.length === 0) return `${cabecalho}:\nSem tarefas neste dia.`;

  const minutos = minhas.reduce((s, t) => s + t.minutos, 0);
  const linhas = minhas.map(
    (t, i) => `${i + 1}. [${t.materia}] ${t.titulo} (${t.minutos} min)\n   Como: ${t.como}\n   Eu preparo: ${t.claude}`,
  );
  return `${cabecalho} (${minutos} min):\n\n${linhas.join('\n\n')}\n\nMeta do dia: ${dia.meta}`;
}
```

- [ ] **Passo 4: rodar e ver passar**

Run: `node --test tests/logic.test.js`
Expected: PASS nos 10 testes. Se `quinta-feira` vier diferente, conferir se o Node tem ICU completo (`node -e "console.log(new Date('2026-11-05T12:00:00').toLocaleDateString('pt-BR',{weekday:'long'}))"`).

- [ ] **Passo 5: rodar a suíte inteira**

Run: `npm test`
Expected: todos os testes das Tarefas 1 a 4 passando.

---

### Tarefa 5: Telas, estilo e navegação

**Arquivos:**
- Modificar: `public/index.html`, `public/css/style.css`, `public/js/app.js`

**Interfaces:**
- Consome: `roadmap.json`, `createStore`, `pickDay`, `hojeISO`, `progresso`, `minutosPorPessoa`, `tarefasPorMateria`, `mensagemDoDia`.
- Produz: o app em `http://localhost:5173` com as rotas por hash abaixo.

**Antes de escrever a interface:** invocar o skill `no-slop-ui` (regras enxutas, bom para um painel de uso próprio) e dizer em uma linha que foi o escolhido e por quê. As regras do `ux-rules.md` e as restrições globais deste plano valem por cima. O que o skill sugerir e contrariar essas regras é vetado, e a resposta final diz o que foi vetado.

**Rotas e telas** (roteador por `location.hash`; rota desconhecida cai em `#/hoje`):

| Rota | Tela | Conteúdo |
|---|---|---|
| `#/hoje` | Hoje | Resolve o dia com `pickDay(hojeISO())`. Se o estado não for `durante`, mostra um aviso no topo dizendo que a data de hoje está fora de 05 a 19/11 e qual dia está sendo exibido. Mostra a tela de dia |
| `#/dia/AAAA-MM-DD` | Dia | Cabeçalho com data por extenso, fase, tipo do dia (execução destacado), meta e dias restantes até 19/11. Duas colunas, Rafael e Charles. Cada tarefa tem caixa de marcar (alvo de 44 px), matéria, minutos, título, "Como fazer" e "Claude entrega". Contador de progresso do dia por pessoa. Botão "Copiar tarefas do Charles" chama `navigator.clipboard.writeText(mensagemDoDia(...))`; sem clipboard ou com erro, mostra o texto numa `textarea` já selecionada e legível. Setas para dia anterior e seguinte |
| `#/roadmap` | Roadmap | Fases em faixa e os 15 dias em grade. Cada dia mostra a data, o tipo, os minutos de cada um e a barra de progresso. Clicar leva a `#/dia/...` |
| `#/materias` | Matérias | Lista das matérias com dono, entregável, formato e tabela de critérios. Cada matéria expande a lista de tarefas ao longo dos dias, com estado marcado ou não |
| `#/equipe` | Equipe | Um cartão por pessoa: nome, RM, papel, matérias, minutos totais, progresso. Abaixo, a divisão do projeto geral |
| `#/resumo` | Resumo | O que é o projeto, o fluxo em etapas (lista numerada em HTML), prazo, riscos e pendências com quem e até quando |

**Layout:** menu lateral fixo à esquerda com os 5 itens (Hoje, Roadmap, Matérias, Equipe, Resumo) e, embaixo, o nome do projeto e "dias restantes". Em largura menor que 760 px o menu vira uma barra no topo com rolagem horizontal só dentro da barra, sem rolagem horizontal na página. Item ativo marcado por cor e por texto, não só por cor.

**Estilo:** fundo claro quente, texto escuro com contraste mínimo 4,5:1, uma cor de destaque verde-azulada (`#1f5f5b`, a do favicon), cinzas quentes. Títulos em fonte com serifa do sistema (`'Iowan Old Style', 'Palatino Linotype', Georgia, serif`), corpo em `system-ui`. Dia de execução em destaque por borda e etiqueta de texto "execução", não só por cor. Foco visível em tudo que se clica. Sem sombras pesadas, sem gradientes.

- [ ] **Passo 1: montar o `index.html` com menu e área principal**

Substituir `<div id="app"></div>` por:

```html
<div class="shell">
  <nav class="menu" aria-label="Principal">
    <a class="marca" href="#/hoje">Marca d'Água</a>
    <ul>
      <li><a href="#/hoje" data-rota="hoje">Hoje</a></li>
      <li><a href="#/roadmap" data-rota="roadmap">Roadmap</a></li>
      <li><a href="#/materias" data-rota="materias">Matérias</a></li>
      <li><a href="#/equipe" data-rota="equipe">Equipe</a></li>
      <li><a href="#/resumo" data-rota="resumo">Resumo</a></li>
    </ul>
    <p class="menu-rodape" id="menu-rodape"></p>
  </nav>
  <main id="app" tabindex="-1"></main>
</div>
```

- [ ] **Passo 2: escrever `app.js`**

Estrutura obrigatória: `carregar()` faz `fetch('data/roadmap.json')`, mostra mensagem de erro com botão "Tentar de novo" se falhar, cria o `store` com `window.localStorage` dentro de `try/catch` (se o acesso lançar, passa `undefined`), e registra `hashchange`. Uma função `renderX(R, store)` por tela, todas montando o DOM com `document.createElement` e `textContent` (sem `innerHTML` com texto dos dados). Ao marcar uma tarefa: `store.toggle(id)` e atualizar os contadores sem recarregar a tela. A cada troca de rota, mover o foco para `#app`.

- [ ] **Passo 3: escrever `style.css` conforme a seção Estilo**

Incluir `@media (prefers-reduced-motion: reduce)` zerando as transições e `@media (max-width: 760px)` para o menu no topo.

- [ ] **Passo 4: verificar no navegador**

Run: `node server.js`, abrir `http://localhost:5173`. Conferir com o navegador embutido (screenshot e `read_page`): as 5 telas abrem, marcar uma tarefa e recarregar mantém a marca, o botão "Copiar tarefas do Charles" copia o texto, e no console do navegador não há erro nem violação de CSP.

- [ ] **Passo 5: cobrir o foco da revisão número 4**

No console do navegador: `Object.defineProperty(navigator, 'clipboard', { value: undefined })` e clicar em "Copiar tarefas do Charles". Esperado: aparece a `textarea` com o texto selecionado e nenhum erro.

---

### Tarefa 6: Revisão de texto, limpeza e verificação final

**Arquivos:**
- Modificar: `public/data/roadmap.json` (só redação), `README.md` (criar, 4 linhas)

- [ ] **Passo 1: humanizar os textos do JSON**

Invocar `humanizer:humanizer` nos campos de prosa de `roadmap.json` (`resumo`, `como`, `claude`, `meta`, `tratamento`). Preservar fatos, números, comandos e nomes de arquivo. Rodar `node --test tests/roadmap.test.js` depois, porque o teste barra travessão e emoji.

- [ ] **Passo 2: remover marcas de IA**

Invocar `anthropic-skills:remove-ai-marks`. Conferir `http://127.0.0.1:8765/health` primeiro. Se não responder, não improvisar limpeza local: registrar na entrega que o passo ficou pendente e que o serviço precisa subir. Se responder, rodar `/inspect` e `/clean` em `public/` (camada A em todos os arquivos, camada B só na prosa de `roadmap.json`).

- [ ] **Passo 3: varrer as proibições de UX**

Run:

```bash
grep -rnE "—|–" public/ ; grep -rnE "rounded-full|border-radius: *(9{2,}|50%)" public/css ; grep -rniE "IntersectionObserver|scroll-?trigger|parallax|<script src=\"http|<link[^>]+href=\"http|@import" public/ ; grep -rnE "style=\"" public/
```

Expected: nenhuma linha. (Os travessões do próprio `plan.md` ficam fora de `public/`.)

- [ ] **Passo 4: verificar em duas larguras (foco da revisão número 5)**

Com o servidor rodando, usar o navegador embutido: `resize_window` com `preset: "desktop"` e depois `preset: "mobile"` (375 px). Em cada uma, abrir as 5 telas e conferir: sem rolagem horizontal na página (`document.documentElement.scrollWidth <= window.innerWidth` no console), menu legível, alvos de 44 px, contraste ok. Voltar ao preset `desktop` ao terminar.

- [ ] **Passo 5: README e rodada final dos testes**

`README.md`:

```markdown
# Dashboard de roadmap, GS2

Roadmap diário da Global Solution 2026.2 para Rafael e Charles.

Para abrir: `node server.js` e acessar http://localhost:5173. O progresso das tarefas fica salvo no navegador.
Os dados estão em `public/data/roadmap.json`. Para rodar os testes: `npm test`.
```

Run: `npm test`
Expected: todos os testes passando.

- [ ] **Passo 6: fechar a entrega**

Responder com o que foi aplicado, o que ficou pendente (serviço do remove-ai-marks, se for o caso), uma linha sobre o que foi vetado do skill de UI e uma linha sobre pendências que dependem da dupla (domínio e termos não se aplicam a uma ferramenta local de uso interno).

---

## Revisão contra o spec

- Seção 10 do spec (dashboard): cobre resumo, membros e funções por matéria, linha do tempo de 05 a 19/11, tarefa diária por pessoa com dias de execução marcados, visão por matéria, cópia da tarefa do Charles e progresso salvo no navegador. Tarefas 2 a 5.
- Seção 8 do spec (fases e datas): fases e dias de execução em 10, 14 e 17/11, travados por teste. Tarefa 2.
- Seção 5 do spec (divisão): donos por matéria conferidos contra os membros por teste. Tarefa 2.
- Seção 2 do spec (restrições de UX e sem CDN): restrições globais e varredura da Tarefa 6.
- Fora deste plano, de propósito: criar o repositório no GitHub e enviar (espera a conta), e o código e os textos de cada matéria, que saem em planos próprios seguindo o roadmap.
