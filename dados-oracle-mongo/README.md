# Cognitive Data Science: Oracle e MongoDB

Entrega de dados do Marca d'Água (Charles Augusto, RM 571908).

| Arquivo | O que é |
|---|---|
| `oracle.sql` | Cria as 6 tabelas (3FN), insere os dados de demonstração e traz 3 consultas. Rodar inteiro com F5 no SQL Developer (Oracle 12c+). |
| `marca_dagua.ddl` | DDL exportado do Data Modeler. Contém linhas de tablespace e usuário do ambiente da FIAP; para criar o banco, use o `oracle.sql`. |
| `marca_dagua.dmd` | Arquivo do Oracle SQL Developer Data Modeler (24.3). É só o ponteiro: o conteúdo do modelo fica na pasta `marca_dagua/`, que precisa acompanhar o arquivo (vai no ZIP da entrega). |
| `modelo-logico.md` | Descrição do modelo lógico e das decisões de modelagem. |
| `mongodb.txt` | Script do mongosh: banco `marca_dagua`, coleções `eventos_brutos` (10) e `relatos` (3), índices e 4 consultas. |
| `json/` | Os mesmos documentos em JSON para importar no Compass (Import Data). |

Id comum entre os bancos: `device_id` (Mongo) = `dispositivo.codigo` (Oracle).
Moradores e relatos são fictícios (LGPD).
