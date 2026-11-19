# Privacidade e LGPD no Marca d'Água (rascunho)

Global Solution 2026.2, Cybersecurity. Rafael Gonçalves (RM 569461) e Charles Augusto (RM 571908).

Este texto é um rascunho para revisão de um advogado. Ele descreve o que o protótipo faz e o que se propõe fazer, e não afirma conformidade com a Lei Geral de Proteção de Dados (Lei 13.709/2018). Atualizado em 16/11/2026 para a nuvem implantada na AWS (API Gateway, Lambda, DynamoDB, CloudWatch e SNS). A versão anterior falava em RDS e em Hugging Face, que saíram do projeto.

## 1. O que existe hoje e o que ainda não existe

O protótipo recebe leituras de um nó simulado e, na nuvem, de um simulador de leituras. A Lambda guarda só a leitura e o risco calculado no DynamoDB. Ela não recebe relato nem coordenada. Quando o risco é de alerta, um alarme do CloudWatch manda e-mail pelo SNS a quem assinou o tópico.

O cadastro de moradores (nome, telefone, e-mail, área e data do consentimento) existe só como modelo no Oracle, com moradores fictícios, e os relatos de texto existem só como exemplos fictícios no MongoDB. Nenhum dos dois está ligado à nuvem. O envio de SMS e a ligação do cadastro ao alerta são evolução futura. O texto abaixo separa o que já trata dado do que só passará a tratar quando o cadastro for ligado ao alerta.

## 2. Quem trata os dados e como falar com essa pessoa

Os responsáveis pelo protótipo são Rafael Gonçalves e Charles Augusto, alunos da FIAP, em um trabalho acadêmico. Canal para pedidos dos titulares: rafa120207@gmail.com, com resposta em até 15 dias.

## 3. Dados, finalidade e base legal proposta

| Dado | Quando existe | Finalidade | Base legal proposta | Onde fica |
|---|---|---|---|---|
| Leitura do nó (nível, chuva, temperatura, umidade, `device_id`, `seq`, hora) e o risco calculado | Hoje | Classificar o risco e manter o histórico | Não é dado pessoal | DynamoDB, CSV da API local |
| E-mail do assinante do alerta | Hoje, na assinatura do tópico SNS | Enviar o aviso de risco | Consentimento (art. 7º, I): a assinatura exige confirmar o link recebido. A proteção da vida (art. 7º, VII) pode se aplicar ao aviso em si | SNS (AWS, região us-east-1) |
| Relato em texto livre | Só com a ligação de relatos reais. Hoje são exemplos fictícios | Dar contexto à leitura | Consentimento (art. 7º, I) | MongoDB de demonstração (fictício) |
| Coordenadas | Não são enviadas pelo nó nem recebidas pela Lambda | Localizar o ponto de risco | Se forem usadas, consentimento. Se apontarem uma residência, é dado pessoal | Não existem hoje na nuvem |
| Nome, telefone e e-mail do cadastro | Só quando o cadastro do Oracle for ligado ao alerta. Hoje são fictícios | Avisar o morador cadastrado | Consentimento (art. 7º, I), com data e hora gravadas | Oracle, com dados fictícios |

A escolha final da base legal de cada linha é do advogado. A proteção da vida é uma hipótese a avaliar para o aviso de risco e não substitui o consentimento para o cadastro.

## 4. Campos do cadastro e a finalidade de cada um

Proposta mínima para quando o cadastro for ligado ao alerta. O modelo Oracle já tem nome, telefone, e-mail, área e data do consentimento, e exige ao menos um entre telefone e e-mail. Cada campo precisa ter uma finalidade que dê para explicar ao morador.

| Campo | Obrigatório | Finalidade |
|---|---|---|
| Telefone ou e-mail | Pelo menos um | Receber o aviso. O e-mail é o canal que funciona hoje, o SMS é evolução futura |
| Área de risco | Sim | Receber aviso do nó certo, sem tratar a localização da casa |
| Nome | Não | O modelo Oracle tem o campo, mas o aviso não usa o nome. Fica fora da proposta mínima |
| Data e hora do consentimento | Sim | Registrar que o morador aceitou |

O que não se pede: CPF, endereço completo, data de nascimento e qualquer dado de saúde. O aviso não usa nada disso.

## 5. Consentimento

Duas situações pedem texto de consentimento. Ambas são propostas de redação.

Na assinatura do alerta por e-mail, antes de pedir o endereço:

> Quero receber avisos de risco de alagamento neste e-mail, e concordo com o uso do meu e-mail só para isso. O serviço de envio fica na AWS, fora do Brasil. Posso cancelar a assinatura quando quiser.

No cadastro com telefone, uma caixa de seleção que vem desmarcada e fica separada de qualquer outro aceite:

> Quero receber avisos de risco de alagamento por mensagem de texto no telefone informado, e concordo com o uso do meu telefone só para isso. Posso retirar o consentimento quando quiser.

Se relatos reais forem ligados ao sistema, o texto antes do campo precisa dizer onde o relato é guardado, pedir que não escreva nome, endereço nem informações de saúde, e informar qualquer serviço externo que o leia. Hoje nenhum serviço de IA lê o relato.

Aviso por mensagem que não seja de risco (novidades, pesquisas) exige consentimento próprio e uma forma simples de sair, e fica fora desta proposta.

## 6. Compartilhamento e fora do Brasil

- Amazon Web Services: hospeda a API, a função, o DynamoDB, os logs e o SNS. É operador. Os recursos estão na região us-east-1, nos Estados Unidos. A telemetria não é dado pessoal, mas o e-mail do assinante é. Guardá-lo no SNS pode contar como transferência internacional de dados (arts. 33 e seguintes), e o aviso do passo 5 existe por isso.
- Defesa Civil: não há integração. Se houver, é preciso base legal e instrumento próprios.
- Nenhum serviço de IA de terceiros lê dado do projeto. A Hugging Face, que recebia o texto do relato na primeira versão da nuvem, saiu do projeto.

## 7. Direitos do titular

O titular pode pedir confirmação de que seus dados são tratados, acesso, correção, eliminação dos dados tratados com consentimento, informação sobre com quem foram compartilhados e a retirada do consentimento (art. 18). A confirmação deve ser imediata ou a declaração completa sair em até 15 dias (art. 19), a conferir com o advogado. Os pedidos chegam pelo canal da seção 2. Hoje não existe rotina para atendê-los. Para o e-mail, o cancelamento é remover a assinatura do tópico SNS. Para o cadastro, apagar por telefone ou e-mail é pendência de quando ele for ligado.

## 8. Quanto tempo os dados ficam

Proposta, a validar: telemetria por 12 meses, logs do CloudWatch por 30 dias, texto livre de relatos por 90 dias e o contato do morador enquanto o cadastro estiver ativo, apagado quando ele cancelar a assinatura ou retirar o consentimento. Esses são os prazos adotados, a conferir com o advogado.

Hoje nenhum desses prazos está configurado. O log do CloudWatch, por padrão, não expira. O relatório de AWS não registra expiração (TTL) na tabela `marca_dagua_leituras`, e sem ela os itens ficam até serem apagados à mão.

## 9. Segurança dos dados

O que já foi feito e conferido no repositório e no relatório de AWS:
- Chave por dispositivo na API e na Lambda (a Lambda responde 401 igual para chave errada e dispositivo desconhecido), chave de leitura separada na API local, limite de requisições e limite de tamanho do corpo.
- HTTPS no endereço do API Gateway, DynamoDB e variáveis de ambiente da Lambda cifrados em repouso.
- Chaves só em variável de ambiente, fora do código e do Git. A chave do dispositivo na nuvem foi rotacionada depois de aparecer em testes.
- A Lambda não tem rota de leitura, não recebe texto livre e não grava coordenada. O log mostra só `device_id`, `seq` e risco, sem a chave e sem o corpo.

O que ainda deixa o dado exposto, e consta no [inventário de ameaças](inventario-ameacas.md): a função usa a LabRole, que é ampla (T03), o e-mail do assinante fica num serviço da AWS fora do Brasil (seção 6), e o aviso chega só a quem assinou o tópico (T14). A API local usa um túnel na demonstração, com chave, mas é um ponto exposto enquanto estiver aberto.

## 10. Crianças e adolescentes

O serviço não é direcionado a menores. Se um cadastro de menor for aceito, o consentimento precisa ser dado por um responsável (art. 14).

## 11. Pendências para a dupla

| Quem | O que |
|---|---|
| Rafael e Charles | Decidir como o morador cancela o cadastro (por telefone ou e-mail) quando ele for ligado ao alerta |
| Rafael e Charles | Decidir quem pode assinar o tópico do SNS e como o assinante dá o consentimento da seção 5 |
| Charles | Configurar a retenção de 30 dias do log no CloudWatch e a expiração (TTL) da tabela do DynamoDB, para os prazos da seção 8 valerem de fato |
| Dupla | Revisão jurídica deste texto e dos termos de uso |
