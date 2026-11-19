// Nó Marca d'Água v2: mede nível, chuva e clima, classifica cada sensor,
// avisa no local (LED e buzzer), imprime o JSON do contrato na serial e
// envia por POST à API. Se o envio falha, a leitura espera numa fila na RAM
// e sai em ordem quando a API volta.
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <time.h>
#include <DHT.h>
#include <ArduinoJson.h>

const int PIN_TRIG = 5;
const int PIN_ECHO = 18;
const int PIN_DHT = 4;
const int PIN_CHUVA = 27;
const int PIN_LED = 26;
const int PIN_BUZZER = 25;

const char* DEVICE_ID = "MD-POA-001";

// Endereço do túnel (cloudflared) até a API. Troque a cada vez que abrir o túnel.
const char* API_URL = "https://SEU-TUNEL.trycloudflare.com/leituras";

// Chave deste dispositivo, a mesma de MD_API_KEYS na API. Cole só no Wokwi, na hora da demonstração,
// e nunca faça commit com a chave real.
const char* API_KEY = "COLE_A_CHAVE_DO_DISPOSITIVO_AQUI";

// Mesmos valores do aws/lambda_ingestao.py. Provisórios até conferir a cota oficial no Gasômetro.
const float NIVEL_ATENCAO_CM = 100;
const float NIVEL_CRITICO_CM = 180;
const float CHUVA_ATENCAO_MMH = 20;
const float CHUVA_CRITICO_MMH = 50;
const float UMIDADE_ATENCAO_PCT = 90;

// HC-SR04 preso a 4 m do fundo da calha: nível = altura - distância medida
const float ALTURA_SENSOR_CM = 400;

// Pluviômetro basculante: cada pulso do botão vale 0,2 mm.
// Com janela de 60 s, 1 pulso = 12 mm/h, 2 pulsos = atenção, 5 pulsos = crítico.
const float MM_POR_PULSO = 0.2;
const unsigned long JANELA_CHUVA_MS = 60000;
const int MAX_PULSOS = 40;

const unsigned long INTERVALO_MS = 2000;

// Fila offline: guarda até 60 leituras (uns 2 min de ciclo). Cheia, perde a mais antiga
// e a API enxerga o buraco na sequência em /indicadores (lacunas_seq).
const int MAX_FILA = 60;
const int REENVIOS_POR_CICLO = 5;
const unsigned long ESPERA_FALHA_MS = 10000;
const int TIMEOUT_HTTP_MS = 4000;

const char* NOMES[] = {"OK", "ATENCAO", "ALERTA"};

volatile unsigned long tempoPulso[MAX_PULSOS];
volatile int idxPulso = 0;
volatile unsigned long ultimoPulso = 0;

DHT dht(PIN_DHT, DHT22);
unsigned long ultimoCiclo = 0;
unsigned long seq = 0;
int riscoAtual = 0;

String fila[MAX_FILA];
int filaIni = 0;
int filaTam = 0;
unsigned long proximaTentativa = 0;

// o botão quica, então ignora pulsos com menos de 50 ms de intervalo
void IRAM_ATTR contaPulso() {
  unsigned long agora = millis();
  if (agora - ultimoPulso > 50) {
    tempoPulso[idxPulso] = agora;
    idxPulso = (idxPulso + 1) % MAX_PULSOS;
    ultimoPulso = agora;
  }
}

float chuvaMmH(unsigned long agora) {
  int n = 0;
  for (int i = 0; i < MAX_PULSOS; i++) {
    unsigned long t = tempoPulso[i];
    if (t != 0 && agora - t <= JANELA_CHUVA_MS) n++;
  }
  return n * MM_POR_PULSO * 3600000.0 / JANELA_CHUVA_MS;
}

float medeDistanciaCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  long duracao = pulseIn(PIN_ECHO, HIGH, 30000);
  return duracao * 0.0343 / 2;
}

// 0 = OK, 1 = ATENCAO, 2 = ALERTA
int classifica(float valor, float atencao, float critico) {
  if (valor >= critico) return 2;
  if (valor >= atencao) return 1;
  return 0;
}

float arredonda(float v) {
  return roundf(v * 10) / 10;
}

void bipe(int ms) {
  for (int i = 0; i < ms; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delayMicroseconds(500);
    digitalWrite(PIN_BUZZER, LOW);
    delayMicroseconds(500);
  }
}

// atenção: 1 bipe curto por ciclo. alerta: 3 bipes. quem não enxerga distingue pelo padrão
void padraoBuzzer(int risco) {
  if (risco == 0) return;
  int vezes = (risco == 2) ? 3 : 1;
  for (int i = 0; i < vezes; i++) {
    bipe(100);
    delay(100);
  }
}

// OK apagado, atenção piscando, alerta aceso fixo
void atualizaLed(int risco) {
  if (risco == 2) digitalWrite(PIN_LED, HIGH);
  else if (risco == 1) digitalWrite(PIN_LED, (millis() / 500) % 2);
  else digitalWrite(PIN_LED, LOW);
}

void sincronizaHora() {
  WiFi.begin("Wokwi-GUEST", "", 6);
  unsigned long ini = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - ini < 8000) delay(200);
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("sem wifi, ts sai nulo");
    return;
  }
  configTime(-3 * 3600, 0, "pool.ntp.org");
  // sem esperar o NTP, a primeira leitura sai com ts nulo e a API recusa (422)
  struct tm t;
  getLocalTime(&t, 5000);
}

String horaIso() {
  struct tm t;
  if (!getLocalTime(&t, 10)) return "";
  char buf[32];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S-03:00", &t);
  return String(buf);
}

// 201 gravou, 409 a API já tinha essa leitura, 422 ela é inválida e repetir não muda nada.
// Nos três casos a leitura sai da fila. Qualquer outra coisa (timeout, 502 do túnel) fica para depois.
bool entregue(int codigo) {
  return codigo == 201 || codigo == 409 || codigo == 422;
}

int enviaPost(const String& corpo) {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    return -1;
  }
  WiFiClientSecure cliente;
  cliente.setInsecure();  // sem validar certificado: serve para a demo, entra como limitação
  HTTPClient http;
  http.setTimeout(TIMEOUT_HTTP_MS);
  if (!http.begin(cliente, API_URL)) return -1;
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  int codigo = http.POST(corpo);
  http.end();
  return codigo;
}

void empilha(const String& corpo) {
  if (filaTam == MAX_FILA) {
    fila[filaIni] = "";
    filaIni = (filaIni + 1) % MAX_FILA;
    filaTam--;
    Serial.println("fila cheia, descartei a leitura mais antiga");
  }
  fila[(filaIni + filaTam) % MAX_FILA] = corpo;
  filaTam++;
}

void esvaziaFila() {
  int enviadas = 0;
  while (filaTam > 0 && enviadas < REENVIOS_POR_CICLO) {
    String corpo = fila[filaIni];
    corpo.replace("\"reenviado\":false", "\"reenviado\":true");
    int codigo = enviaPost(corpo);
    if (!entregue(codigo)) {
      proximaTentativa = millis() + ESPERA_FALHA_MS;
      Serial.printf("reenvio falhou (%d), fila com %d\n", codigo, filaTam);
      return;
    }
    fila[filaIni] = "";
    filaIni = (filaIni + 1) % MAX_FILA;
    filaTam--;
    enviadas++;
    Serial.printf("reenviada da fila: HTTP %d, restam %d\n", codigo, filaTam);
    Serial.println(corpo);
  }
}

// Com a fila vazia manda direto. Com fila, a leitura nova entra no fim para não furar a ordem.
void entrega(const String& corpo) {
  bool podeTentar = millis() >= proximaTentativa;
  if (filaTam == 0 && podeTentar) {
    int codigo = enviaPost(corpo);
    if (entregue(codigo)) {
      Serial.printf("enviada: HTTP %d\n", codigo);
      return;
    }
    proximaTentativa = millis() + ESPERA_FALHA_MS;
    empilha(corpo);
    Serial.printf("envio falhou (%d), leitura na fila (%d)\n", codigo, filaTam);
    return;
  }
  empilha(corpo);
  if (podeTentar) esvaziaFila();
  else Serial.printf("API fora, leitura na fila (%d)\n", filaTam);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_CHUVA, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_CHUVA), contaPulso, FALLING);
  dht.begin();

  digitalWrite(PIN_LED, HIGH);
  bipe(200);
  digitalWrite(PIN_LED, LOW);
  Serial.println("no iniciado");

  sincronizaHora();
  ultimoCiclo = millis() - INTERVALO_MS;
}

void loop() {
  unsigned long agora = millis();

  if (agora - ultimoCiclo >= INTERVALO_MS) {
    ultimoCiclo = agora;

    float dist = medeDistanciaCm();
    bool nivelValido = dist > 0;  // 0 = eco não voltou, não vale como nível
    float nivel = nivelValido ? max(0.0f, ALTURA_SENSOR_CM - dist) : NAN;
    float chuva = chuvaMmH(agora);
    float temp = dht.readTemperature();
    float umid = dht.readHumidity();

    int sNivel = nivelValido ? classifica(nivel, NIVEL_ATENCAO_CM, NIVEL_CRITICO_CM) : 0;
    int sChuva = classifica(chuva, CHUVA_ATENCAO_MMH, CHUVA_CRITICO_MMH);
    int sUmid = (umid >= UMIDADE_ATENCAO_PCT) ? 1 : 0;
    int risco = max(sNivel, sChuva);  // umidade só informa, não dispara alarme
    riscoAtual = risco;

    JsonDocument doc;
    doc["device_id"] = DEVICE_ID;
    doc["seq"] = ++seq;
    String ts = horaIso();
    if (ts.length() > 0) doc["ts"] = ts;
    else doc["ts"] = nullptr;
    doc["nivel_cm"] = arredonda(nivel);
    doc["chuva_mm_h"] = arredonda(chuva);
    doc["temperatura_c"] = arredonda(temp);
    doc["umidade_pct"] = arredonda(umid);
    JsonObject status = doc["status"].to<JsonObject>();
    status["nivel"] = NOMES[sNivel];
    status["chuva"] = NOMES[sChuva];
    status["umidade"] = NOMES[sUmid];
    doc["risco"] = NOMES[risco];
    doc["reenviado"] = false;

    Serial.printf("[%s] nivel=%.1f cm | chuva=%.1f mm/h | %.1f C | %.0f%%\n",
                  NOMES[risco], nivel, chuva, temp, umid);
    String corpo;
    serializeJson(doc, corpo);
    Serial.println(corpo);

    entrega(corpo);
    padraoBuzzer(risco);
  }

  atualizaLed(riscoAtual);
}
