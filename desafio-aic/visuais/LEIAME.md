# Material visual do pitch de AI Challenges

Tudo em 1920x1080. Os PNGs saem de `_work/frames.tpl.html` (rode `python _work/build_frames.py` para refazer) e os clipes do Wokwi foram gravados por uma simulação real, sem edição.

## Ordem do vídeo

| Bloco do roteiro | Arquivo | Observação |
|---|---|---|
| 0:00 abertura | `01-capa.png` | Volta no fim, por pelo menos 8 s |
| 0:20 problema, público, solução | `02-problema-publico-solucao.png` | |
| 1:05 ODS | `03-ods.png` | Cores próprias, não é o logo oficial da ONU |
| 1:20 ideias da live | `04-ideias-da-live.png` | Sem nome de quem falou, porque não foi confirmado |
| 1:35 arquitetura | `05a-arquitetura-no-api-nuvem.png`, depois `05b-arquitetura-completa.png` | 05b só acrescenta dados e modelos |
| 2:00 UML | `06-uml-sequencia.png` | É o PNG de `docs/` sobre fundo escuro |
| 2:20 Wokwi | `wokwi-1-no-normal.mp4`, `wokwi-2-chuva-forte.mp4`, `wokwi-3-nivel-critico.mp4` | 12 s, 25 s e 23 s, sem áudio |
| 3:15 nuvem | `07-aws-1-teste-simulador.png`, `07-aws-2-dynamodb.png`, `07-aws-3-cloudwatch.png`, `07-aws-4-email-sns.png` | Recortes das capturas de `aws/evidencias/` |
| 4:20 dados | `08a-oracle-consulta-3.png`, `08b-mongodb-consulta.png`, `09-ml-pr-auc.png`, `10-rna-tabela-teste.png` | Oracle e Mongo, uns 6 s cada |
| 5:07 gestão | `13-roadmap-dashboard-progresso-zerado.png` | Ver aviso abaixo, melhor regravar |
| 5:47 futuro e segurança | `11-implementado-e-evolucao.png`, `12-prova-protecao-api.png` | A prova usa a saída salva em `ciberseguranca/evidencias/` |
| 6:30 fecho | `01-capa.png` | |

## O que veio de execução real

- Oracle: o `oracle.sql` inteiro rodou num Oracle Database Free (imagem `gvenzl/oracle-free:slim-faststart`, contêiner já removido). A tela mostra a consulta 3 e o resultado exato do sqlplus. Os dados de demonstração incluem uma notificação por SMS marcada como ENVIADA, então não fale em SMS como se existisse de verdade: no pitch o SMS é evolução futura.
- MongoDB: o `mongodb.txt` rodou num contêiner `mongo:7` descartável (já removido). A tela mostra a consulta 4 do arquivo, só com a indentação reorganizada para caber, e a saída exata do mongosh.
- Wokwi: o `sketch.ino` e o `diagram.json` do repositório foram carregados sem alteração num projeto anônimo do Wokwi, com as bibliotecas DHT sensor library e ArduinoJson. O projeto da sua conta não foi tocado.
- ML e rede neural: o gráfico e a tabela vêm das saídas salvas nos notebooks.

## Pendências

1. Print do Kanban do Charles.
2. Dashboard de roadmap: o arquivo abre sem o progresso (ele fica no localStorage do seu navegador), então a captura mostra "0 de N feitas" em todos os dias. O card "Modelos e armazenamento" (11/11 a 14/11) também ainda diz "RDS criado", que contradiz o DynamoDB. Abra `Dashboard GS2.html` no seu navegador, vá em Roadmap e grave daí.
3. Seu rosto no canto da tela: isso só você grava. Os quadros usam a tela inteira, então reduza ou deslize o vídeo da câmera na edição.

## Pontos para conferir antes de narrar

- Nos clipes do Wokwi, cada clique no botão conta dois pulsos (24 mm/h por clique). Cinco cliques mostram `chuva=120.0`, não 60 como diz `aicss-sensores/roteiro-cenarios.md`. Sua captura de 09/11 já mostrava 120. A fala "passam de 50 mm/h" continua certa; só não leia "60" em voz alta.
- O nó está sem API no Wokwi (a URL é o texto de exemplo do sketch), então a serial mostra "API fora, leitura na fila" e as primeiras leituras saem com `"ts":null`. Combina com "o alerta local não depende de internet".
- O buzzer aparece só como a notinha azul quando toca. O Wokwi gravado não tem som.
- As capturas da AWS têm texto pequeno. Os recortes ajudam, mas dá para dar zoom lento na edição.
- O áudio do pitch (`AUDIO AIC PRA VIDEO GS2.ogg`) tem 5:20, abaixo dos 6:40 do roteiro. Sobra margem para mostrar mais tempo de Wokwi.
