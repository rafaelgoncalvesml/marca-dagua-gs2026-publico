# Marca d'Água

Global Solution 2026.2, FIAP. Tema CitizenTech.

Um nó comunitário com ESP32 mede o nível da água e a chuva em áreas de risco de Porto Alegre, avisa no local mesmo sem internet e envia as leituras a uma API. Modelos de ML e de rede neural estimam o risco de alagamento para as próximas horas, e um fluxo na AWS avisa os moradores cadastrados.

Rafael Gonçalves (RM 569461) e Charles Augusto (RM 571908).

O desenho completo está em [docs/superpowers/specs](docs/superpowers/specs/2026-11-05-marca-dagua-design.md). As pastas por matéria entram conforme cada entrega fecha.

- [python-api](python-api): API FastAPI que recebe as leituras, classifica, grava em CSV e calcula indicadores (Computational Thinking with Python).
