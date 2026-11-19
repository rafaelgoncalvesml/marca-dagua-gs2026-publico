-- =====================================================================
-- Marca d'Água - Cognitive Data Science (Oracle)
-- Modelo relacional em 3FN com 6 tabelas.
-- Como rodar no SQL Developer: abra este arquivo, selecione a conexão
-- e use "Executar Script" (F5). Rode o arquivo inteiro de uma vez.
-- Requer Oracle 12c ou mais novo (colunas IDENTITY).
-- Os dados de moradores são de demonstração (fictícios, por causa da LGPD).
-- As leituras vêm do script de cenários da API (python-api/cenarios.py).
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. Limpeza (permite rodar o script mais de uma vez)
-- ---------------------------------------------------------------------
BEGIN
  FOR t IN (SELECT column_value AS nome
              FROM TABLE(sys.odcivarchar2list(
                     'NOTIFICACAO', 'ALERTA', 'LEITURA', 'MORADOR', 'DISPOSITIVO', 'AREA_RISCO'))) LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP TABLE ' || t.nome || ' CASCADE CONSTRAINTS PURGE';
    EXCEPTION
      WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;  -- ignora "tabela não existe"
    END;
  END LOOP;
END;
/

-- ---------------------------------------------------------------------
-- 1. Criação das tabelas
-- ---------------------------------------------------------------------

-- Áreas de risco atendidas (ilhas, Sarandi, Humaitá...)
CREATE TABLE area_risco (
  id_area  NUMBER GENERATED ALWAYS AS IDENTITY,
  nome     VARCHAR2(80) NOT NULL,
  bairro   VARCHAR2(60) NOT NULL,
  CONSTRAINT pk_area_risco PRIMARY KEY (id_area),
  CONSTRAINT uq_area_risco_nome UNIQUE (nome)
);

-- Nós comunitários com ESP32. "codigo" é o device_id do JSON.
CREATE TABLE dispositivo (
  id_dispositivo  NUMBER GENERATED ALWAYS AS IDENTITY,
  codigo          VARCHAR2(40) NOT NULL,
  id_area         NUMBER NOT NULL,
  instalado_em    DATE,
  ativo           NUMBER(1) DEFAULT 1 NOT NULL,
  CONSTRAINT pk_dispositivo PRIMARY KEY (id_dispositivo),
  CONSTRAINT uq_dispositivo_codigo UNIQUE (codigo),
  CONSTRAINT fk_dispositivo_area FOREIGN KEY (id_area) REFERENCES area_risco (id_area),
  CONSTRAINT ck_dispositivo_ativo CHECK (ativo IN (0, 1))
);

-- Leituras enviadas pelo nó. Mesmos limites de validação da API.
-- (id_dispositivo, seq) é único: é a regra que faz a API devolver 409.
CREATE TABLE leitura (
  id_leitura      NUMBER GENERATED ALWAYS AS IDENTITY,
  id_dispositivo  NUMBER NOT NULL,
  seq             NUMBER(15) NOT NULL,
  ts_leitura      TIMESTAMP WITH TIME ZONE NOT NULL,
  nivel_cm        NUMBER(6,1) NOT NULL,
  chuva_mm_h      NUMBER(5,1) NOT NULL,
  temperatura_c   NUMBER(4,1) NOT NULL,
  umidade_pct     NUMBER(4,1) NOT NULL,
  reenviado       NUMBER(1) DEFAULT 0 NOT NULL,
  risco           VARCHAR2(7) NOT NULL,
  recebido_em     TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT pk_leitura PRIMARY KEY (id_leitura),
  CONSTRAINT uq_leitura_dispositivo_seq UNIQUE (id_dispositivo, seq),
  CONSTRAINT fk_leitura_dispositivo FOREIGN KEY (id_dispositivo) REFERENCES dispositivo (id_dispositivo),
  CONSTRAINT ck_leitura_nivel CHECK (nivel_cm BETWEEN 0 AND 1000),
  CONSTRAINT ck_leitura_chuva CHECK (chuva_mm_h BETWEEN 0 AND 500),
  CONSTRAINT ck_leitura_temperatura CHECK (temperatura_c BETWEEN -20 AND 60),
  CONSTRAINT ck_leitura_umidade CHECK (umidade_pct BETWEEN 0 AND 100),
  CONSTRAINT ck_leitura_reenviado CHECK (reenviado IN (0, 1)),
  CONSTRAINT ck_leitura_risco CHECK (risco IN ('OK', 'ATENCAO', 'ALERTA'))
);

-- Moradores cadastrados para receber aviso. Dado pessoal: só o necessário,
-- com a data do consentimento (LGPD) e ao menos um canal de contato.
CREATE TABLE morador (
  id_morador       NUMBER GENERATED ALWAYS AS IDENTITY,
  nome             VARCHAR2(100) NOT NULL,
  telefone         VARCHAR2(20),
  email            VARCHAR2(120),
  id_area          NUMBER NOT NULL,
  consentimento_em TIMESTAMP WITH TIME ZONE NOT NULL,
  CONSTRAINT pk_morador PRIMARY KEY (id_morador),
  CONSTRAINT fk_morador_area FOREIGN KEY (id_area) REFERENCES area_risco (id_area),
  CONSTRAINT ck_morador_contato CHECK (telefone IS NOT NULL OR email IS NOT NULL)
);

-- Alerta emitido a partir de uma leitura em risco ALERTA.
-- O nível do alerta é o risco da leitura, por isso não é repetido aqui (3FN).
CREATE TABLE alerta (
  id_alerta   NUMBER GENERATED ALWAYS AS IDENTITY,
  id_leitura  NUMBER NOT NULL,
  emitido_em  TIMESTAMP WITH TIME ZONE NOT NULL,
  mensagem    VARCHAR2(300) NOT NULL,
  CONSTRAINT pk_alerta PRIMARY KEY (id_alerta),
  CONSTRAINT uq_alerta_leitura UNIQUE (id_leitura),
  CONSTRAINT fk_alerta_leitura FOREIGN KEY (id_leitura) REFERENCES leitura (id_leitura)
);

-- Cada aviso enviado a um morador por um canal (tabela associativa
-- entre alerta e morador, com dados próprios do envio).
CREATE TABLE notificacao (
  id_notificacao  NUMBER GENERATED ALWAYS AS IDENTITY,
  id_alerta       NUMBER NOT NULL,
  id_morador      NUMBER NOT NULL,
  canal           VARCHAR2(5) NOT NULL,
  enviada_em      TIMESTAMP WITH TIME ZONE NOT NULL,
  status_envio    VARCHAR2(7) NOT NULL,
  CONSTRAINT pk_notificacao PRIMARY KEY (id_notificacao),
  CONSTRAINT uq_notificacao_envio UNIQUE (id_alerta, id_morador, canal),
  CONSTRAINT fk_notificacao_alerta FOREIGN KEY (id_alerta) REFERENCES alerta (id_alerta),
  CONSTRAINT fk_notificacao_morador FOREIGN KEY (id_morador) REFERENCES morador (id_morador),
  CONSTRAINT ck_notificacao_canal CHECK (canal IN ('SMS', 'EMAIL')),
  CONSTRAINT ck_notificacao_status CHECK (status_envio IN ('ENVIADA', 'FALHA'))
);

-- Índices nas chaves estrangeiras mais consultadas
CREATE INDEX ix_dispositivo_area ON dispositivo (id_area);
CREATE INDEX ix_leitura_ts ON leitura (ts_leitura);
CREATE INDEX ix_morador_area ON morador (id_area);
CREATE INDEX ix_notificacao_morador ON notificacao (id_morador);

-- ---------------------------------------------------------------------
-- 2. Dados
-- ---------------------------------------------------------------------

INSERT INTO area_risco (nome, bairro) VALUES ('Ilhas', 'Arquipélago');
INSERT INTO area_risco (nome, bairro) VALUES ('Sarandi', 'Sarandi');
INSERT INTO area_risco (nome, bairro) VALUES ('Humaitá', 'Humaitá');

-- O nó de demonstração do projeto. A área é a de demonstração (Ilhas).
INSERT INTO dispositivo (codigo, id_area, instalado_em)
SELECT 'MD-POA-001', id_area, DATE '2026-11-10'
  FROM area_risco WHERE nome = 'Ilhas';

-- As 3 leituras dos cenários da API (normal, atenção e alerta).
INSERT INTO leitura (id_dispositivo, seq, ts_leitura, nivel_cm, chuva_mm_h, temperatura_c, umidade_pct,
                     reenviado, risco, recebido_em)
SELECT id_dispositivo, 1794282380, TIMESTAMP '2026-11-10 00:46:19 -03:00', 45.0, 0.4, 24.1, 62.0,
       0, 'OK', TIMESTAMP '2026-11-10 03:46:19 +00:00'
  FROM dispositivo WHERE codigo = 'MD-POA-001';

INSERT INTO leitura (id_dispositivo, seq, ts_leitura, nivel_cm, chuva_mm_h, temperatura_c, umidade_pct,
                     reenviado, risco, recebido_em)
SELECT id_dispositivo, 1794282381, TIMESTAMP '2026-11-10 00:46:19 -03:00', 135.0, 18.0, 22.5, 91.0,
       0, 'ATENCAO', TIMESTAMP '2026-11-10 03:46:19 +00:00'
  FROM dispositivo WHERE codigo = 'MD-POA-001';

INSERT INTO leitura (id_dispositivo, seq, ts_leitura, nivel_cm, chuva_mm_h, temperatura_c, umidade_pct,
                     reenviado, risco, recebido_em)
SELECT id_dispositivo, 1794282382, TIMESTAMP '2026-11-10 00:46:19 -03:00', 195.5, 42.0, 21.0, 97.0,
       0, 'ALERTA', TIMESTAMP '2026-11-10 03:46:19 +00:00'
  FROM dispositivo WHERE codigo = 'MD-POA-001';

-- Moradores de demonstração (fictícios; nenhum dado pessoal real).
INSERT INTO morador (nome, telefone, email, id_area, consentimento_em)
SELECT 'Morador Demo 1', NULL, 'morador.demo1@example.com', id_area, TIMESTAMP '2026-11-10 09:00:00 -03:00'
  FROM area_risco WHERE nome = 'Ilhas';
INSERT INTO morador (nome, telefone, email, id_area, consentimento_em)
SELECT 'Morador Demo 2', '+5551000000002', 'morador.demo2@example.com', id_area, TIMESTAMP '2026-11-10 09:05:00 -03:00'
  FROM area_risco WHERE nome = 'Ilhas';
INSERT INTO morador (nome, telefone, email, id_area, consentimento_em)
SELECT 'Morador Demo 3', '+5551000000003', NULL, id_area, TIMESTAMP '2026-11-10 09:10:00 -03:00'
  FROM area_risco WHERE nome = 'Sarandi';

-- Alerta da leitura em risco ALERTA e o aviso aos moradores da área do nó.
INSERT INTO alerta (id_leitura, emitido_em, mensagem)
SELECT l.id_leitura, TIMESTAMP '2026-11-10 00:46:20 -03:00',
       'Risco de alagamento na sua área. Siga para um local seguro e ligue 199.'
  FROM leitura l
  JOIN dispositivo d ON d.id_dispositivo = l.id_dispositivo
 WHERE d.codigo = 'MD-POA-001' AND l.seq = 1794282382;

INSERT INTO notificacao (id_alerta, id_morador, canal, enviada_em, status_envio)
SELECT a.id_alerta, m.id_morador, 'EMAIL', TIMESTAMP '2026-11-10 00:46:21 -03:00', 'ENVIADA'
  FROM alerta a, morador m
 WHERE m.nome = 'Morador Demo 1';
INSERT INTO notificacao (id_alerta, id_morador, canal, enviada_em, status_envio)
SELECT a.id_alerta, m.id_morador, 'SMS', TIMESTAMP '2026-11-10 00:46:21 -03:00', 'ENVIADA'
  FROM alerta a, morador m
 WHERE m.nome = 'Morador Demo 2';

COMMIT;

-- ---------------------------------------------------------------------
-- 3. Consultas
-- ---------------------------------------------------------------------

-- Consulta 1: leituras que pedem atenção ou alerta, com dispositivo e área
-- (junção de 3 tabelas, filtro e ordenação).
SELECT a.nome        AS area,
       d.codigo      AS dispositivo,
       l.seq,
       l.ts_leitura,
       l.nivel_cm,
       l.chuva_mm_h,
       l.risco
  FROM leitura l
  JOIN dispositivo d ON d.id_dispositivo = l.id_dispositivo
  JOIN area_risco a  ON a.id_area = d.id_area
 WHERE l.risco IN ('ATENCAO', 'ALERTA')
 ORDER BY l.nivel_cm DESC;

-- Consulta 2: resumo por área e por risco (agregação com GROUP BY).
SELECT a.nome                      AS area,
       l.risco,
       COUNT(*)                    AS total_leituras,
       MAX(l.nivel_cm)             AS nivel_maximo_cm,
       ROUND(AVG(l.chuva_mm_h), 1) AS chuva_media_mm_h
  FROM leitura l
  JOIN dispositivo d ON d.id_dispositivo = l.id_dispositivo
  JOIN area_risco a  ON a.id_area = d.id_area
 GROUP BY a.nome, l.risco
 ORDER BY a.nome, MAX(l.nivel_cm) DESC;

-- Consulta 3: quem foi avisado em cada alerta (junção de 5 tabelas).
SELECT al.id_alerta,
       d.codigo        AS dispositivo,
       l.risco,
       m.nome          AS morador,
       n.canal,
       n.status_envio,
       n.enviada_em
  FROM notificacao n
  JOIN alerta al      ON al.id_alerta = n.id_alerta
  JOIN leitura l      ON l.id_leitura = al.id_leitura
  JOIN dispositivo d  ON d.id_dispositivo = l.id_dispositivo
  JOIN morador m      ON m.id_morador = n.id_morador
 ORDER BY al.id_alerta, m.nome;
