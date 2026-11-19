# Roteiro dos cenários no Wokwi (dia 08/11)

Objetivo: provocar o nó nos comportamentos 2 e 3 e guardar, para cada um, o print do LED e do buzzer e o JSON da saída serial. O comportamento 1 (tudo normal) já foi capturado no dia 06/11.

## Limiares usados

São os mesmos do `aws/lambda_ingestao.py` e das constantes do `sketch.ino`. Seguem provisórios até conferir a cota oficial.

| Medida | Atenção | Alerta | Como o sketch calcula |
|---|---|---|---|
| Nível da água | 100 cm ou mais | 180 cm ou mais | 400 cm (altura do sensor) menos a distância medida pelo HC-SR04 |
| Chuva | 20 mm/h ou mais | 50 mm/h ou mais | pulsos do botão na janela de 60 s, 0,2 mm por pulso, ou seja 12 mm/h por pulso |
| Umidade | 90% ou mais | não existe | só informa, não dispara alarme |

O risco do nó é o pior entre nível e chuva. Cada nível de risco tem um padrão de aviso:

| Risco | LED | Buzzer |
|---|---|---|
| OK | apagado | mudo |
| ATENCAO | piscando | 1 bipe curto por ciclo |
| ALERTA | aceso fixo | 3 bipes por ciclo |

O ciclo de leitura é de 2 s. Cada linha de saída serial tem o formato `[RISCO] nivel=... | chuva=... | temp | umidade`, seguida do JSON.

Tabela de pulsos (chuva): 1 pulso = 12 mm/h (OK), 2 = 24, 3 = 36, 4 = 48 (todos ATENCAO), 5 = 60 (ALERTA). Só 5 pulsos passam do limiar de alerta, e os 5 precisam cair dentro de 60 s.

## Antes de cada cenário

1. Reinicie a simulação (botão de parar e rodar de novo). Isso zera os pulsos antigos do pluviômetro.
2. Deixe o HC-SR04 em 350 cm (valor inicial do `diagram.json`), exceto no cenário que manda mexer nele.
3. Espere aparecer `no iniciado` e a primeira linha `[OK]`.

## Comportamento 2: chuva forte (ALERTA por chuva)

1. Com o sensor em 350 cm, clique no botão azul do pluviômetro 5 vezes, uma vez por segundo, aproximadamente. Termine em menos de 30 s.
2. Na saída serial, a linha vai passar por `chuva=12.0` e `24.0` (ATENCAO) até chegar em `chuva=60.0` com `[ALERTA]`.
3. Capture dentro de 60 s depois do primeiro clique. Passado isso, os pulsos saem da janela e o risco desce sozinho.
4. Para o buzzer, que só toca 3 bipes de 100 ms, veja a observação abaixo.

JSON esperado (o `ts` e o `seq` mudam, o nível fica perto de 47 cm):

```json
{"device_id":"MD-POA-001","seq":N,"ts":"2026-11-08T..-03:00","nivel_cm":47.3,"chuva_mm_h":60,"temperatura_c":24,"umidade_pct":70,"status":{"nivel":"OK","chuva":"ALERTA","umidade":"OK"},"risco":"ALERTA","reenviado":false}
```

## Comportamento 3: nível crítico (ALERTA por nível)

1. Reinicie e espere a primeira linha `[OK]`.
2. Clique no sensor HC-SR04 e arraste o controle de distância (`Distance`) para 190 cm.
3. A saída deve mostrar `nivel` por volta de 208 cm e `[ALERTA]`. Em 190 cm há folga de sobra: o Wokwi lê uns 1,5 a 2,5 cm acima do valor ajustado, e o alerta começa em 180 cm de nível, que equivale a ajustar uns 217 cm ou menos.
4. LED aceso fixo e 3 bipes por ciclo. Chuva fica em 0.

JSON esperado:

```json
{"device_id":"MD-POA-001","seq":N,"ts":"2026-11-08T..-03:00","nivel_cm":208.6,"chuva_mm_h":0,"temperatura_c":24,"umidade_pct":70,"status":{"nivel":"ALERTA","chuva":"OK","umidade":"OK"},"risco":"ALERTA","reenviado":false}
```

O valor exato de `nivel_cm` pode variar uma casa decimal.

## Variantes de atenção (opcionais, 5 minutos)

Servem para mostrar o LED piscando, que no dia 06/11 saiu apagado no print.

| Gatilho | Como provocar | Esperado |
|---|---|---|
| Nível | HC-SR04 em 280 cm | `nivel` perto de 118 cm, status nível ATENCAO |
| Chuva | 2 a 4 cliques no botão em até 60 s | `chuva` 24.0, 36.0 ou 48.0, status chuva ATENCAO |

Em ambas, risco ATENCAO, LED piscando e 1 bipe por ciclo.

## Como registrar cada caso

Salve em `aicss-sensores/evidencias/` com nomes que dizem o cenário, por exemplo `02-chuva-forte-led-serial.png`, `02-chuva-forte-buzzer.png`, `03-nivel-critico-led-serial.png`, `03-nivel-critico-buzzer.png`, e um `02-chuva-forte.json` e `03-nivel-critico.json` com a linha de JSON copiada da serial.

Sobre o buzzer: o ícone dele só mostra o som enquanto o bipe toca, e cada bipe dura 100 ms. Um print comum tende a pegar o buzzer calado. Duas formas de resolver:

- gravar a tela por 10 s (Win + Shift + R, ou Xbox Game Bar com Win + G) e tirar o quadro em que o buzzer aparece tocando;
- ou fazer vários prints seguidos e ficar com o que mostrar as ondas de som ao lado do buzzer.

O LED aceso fixo no alerta não tem esse problema. No ATENCAO ele pisca a cada 500 ms, então pode precisar de mais de um print também.

## Conferência final

- Os dois JSONs têm `risco` igual a `ALERTA` e o `status` do sensor certo (chuva no cenário 2, nível no 3).
- Cada print mostra LED e linha serial `[ALERTA]` no mesmo quadro.
- Os quatro arquivos estão na pasta de evidências, nomeados por cenário.
