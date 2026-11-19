# Marca d'Água: modelo de dados (Cognitive Data Science)

Modelo lógico e relacional em 3FN com 6 tabelas no Oracle, mais o MongoDB para eventos e relatos. O script que cria tudo é o `oracle.sql`.

## 1. As 6 entidades

| Entidade | Papel | Chave primária | Atributos |
|---|---|---|---|
| AREA_RISCO | Área de risco atendida (ilhas, Sarandi, Humaitá) | id_area | nome (único), bairro |
| DISPOSITIVO | Nó comunitário com ESP32 | id_dispositivo | codigo (único, é o `device_id` do JSON), instalado_em, ativo; FK id_area |
| LEITURA | Leitura enviada pelo nó | id_leitura | seq, ts_leitura, nivel_cm, chuva_mm_h, temperatura_c, umidade_pct, reenviado, risco, recebido_em; FK id_dispositivo; único (id_dispositivo, seq) |
| MORADOR | Morador cadastrado para receber aviso | id_morador | nome, telefone, email, consentimento_em; FK id_area |
| ALERTA | Alerta emitido por uma leitura em risco ALERTA | id_alerta | emitido_em, mensagem; FK id_leitura (único) |
| NOTIFICACAO | Aviso enviado a um morador por um canal | id_notificacao | canal (SMS ou EMAIL), enviada_em, status_envio; FK id_alerta, id_morador; único (id_alerta, id_morador, canal) |

## 2. Relacionamentos e cardinalidades

| Relacionamento | Cardinalidade | Leitura |
|---|---|---|
| AREA_RISCO tem DISPOSITIVO | 1 para N | Uma área tem vários nós; cada nó fica em uma área. |
| AREA_RISCO abriga MORADOR | 1 para N | Uma área abriga vários moradores; cada morador pertence a uma área. |
| DISPOSITIVO envia LEITURA | 1 para N | Um nó envia muitas leituras; cada leitura vem de um nó. |
| LEITURA gera ALERTA | 1 para 0 ou 1 | Só a leitura em risco ALERTA gera alerta, e no máximo um. |
| ALERTA dispara NOTIFICACAO | 1 para N | Um alerta avisa vários moradores. |
| MORADOR recebe NOTIFICACAO | 1 para N | Um morador recebe avisos de vários alertas. |

ALERTA e MORADOR se relacionam de N para N, resolvido pela tabela associativa NOTIFICACAO, que guarda os dados do próprio envio (canal, horário e status).

## 3. Por que está em 3FN

- **1FN:** todos os atributos são atômicos. Telefone e e-mail são colunas separadas, e não há grupos repetidos.
- **2FN:** as tabelas com chave composta natural usam chave substituta (`id_*`), então nenhum atributo depende de parte da chave. As combinações naturais (`id_dispositivo` + `seq`, por exemplo) ficam como restrição `UNIQUE`.
- **3FN:** nenhum atributo depende de outro atributo que não seja a chave.
  - O nome e o bairro da área ficam só em AREA_RISCO. A leitura não os repete: chega à área por LEITURA, DISPOSITIVO e AREA_RISCO.
  - O nível do alerta não é guardado em ALERTA, porque é o `risco` da leitura. Guardar de novo criaria uma dependência transitiva.
  - O nome do morador fica só em MORADOR, e a notificação aponta para ele.

Uma escolha consciente: `risco` fica em LEITURA mesmo sendo calculável pelos limiares. Os limiares da API ainda são provisórios, e o risco registrado é o que valeu na hora da leitura.

## 4. Distribuição entre Oracle e MongoDB

| Dado | Onde | Justificativa |
|---|---|---|
| Áreas, dispositivos, moradores | Oracle | Cadastro com integridade referencial e consentimento (LGPD). |
| Leituras validadas | Oracle | Campos fixos, consultas agregadas e a regra única (dispositivo, seq). |
| Alertas e notificações | Oracle | Trilha de auditoria de quem foi avisado, com chaves ligadas. |
| Eventos brutos do nó | MongoDB | O JSON completo, com o status de cada sensor, que pode ganhar campos conforme o sensor evolui. |
| Relatos de moradores | MongoDB | Texto livre com campos opcionais (local, tipo, observação), sem esquema fixo. |

O **id comum** entre os dois bancos é o `device_id` (por exemplo `MD-POA-001`): no Oracle ele é `dispositivo.codigo`, e no MongoDB é o campo `device_id` de cada documento. A demonstração cruzada consulta o dispositivo e sua área no Oracle e, com o mesmo código, os eventos e relatos no MongoDB.

## 5. Passo a passo no Oracle SQL Developer Data Modeler

1. Abra o Data Modeler e crie um design novo. Salve já com o nome do projeto.
2. No modelo **lógico**, crie as 6 entidades da tabela da seção 1 com seus atributos. Marque os identificadores únicos (UID) como chave primária.
3. Crie os relacionamentos 1 para N da seção 2, sempre do lado "1" para o lado "N", e marque como obrigatório o lado que tem a chave estrangeira. O relacionamento entre ALERTA e LEITURA é 1 para 0 ou 1.
4. Para NOTIFICACAO, crie as duas ligações 1 para N (com ALERTA e com MORADOR). Isso faz ela virar a tabela associativa.
5. Use **Engineer to Relational Model** para gerar o modelo relacional. Confira os nomes, os tipos, as chaves primárias e as estrangeiras.
6. Ajuste os tipos conforme o `oracle.sql` (por exemplo `TIMESTAMP WITH TIME ZONE` nas datas de leitura) e confira as restrições de unicidade.
7. Exporte o DDL (File > Export > DDL File) e salve o design como `.dmd`. Guarde os dois na pasta `dados-oracle-mongo/`.
8. Compare o DDL exportado com o `oracle.sql`. O `oracle.sql` é a versão de referência, então ajuste o modelo se houver diferença.
