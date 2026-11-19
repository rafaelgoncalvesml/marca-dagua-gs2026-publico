"""Gera o PDF do relatório de Cybersecurity a partir de relatorio.html.

Uso: python gerar_pdf.py

Diretivas do modelo:
  <!--IMG arquivo.png|legenda-->   lê o print de ../evidencias/ pelo nome; se ainda não existe, vira
                                   uma caixa amarela com o nome esperado (salve o print e rode de novo)
  <!--TXT caminho/do/arquivo-->    insere o texto de um arquivo do repositório, em bloco de código
  <!--DECIDIR texto-->             caixa amarela com uma decisão que a dupla ainda precisa tomar;
                                   apague a linha do modelo quando decidir
Precisa do Chrome ou do Edge instalado (impressão headless em PDF).
"""
import base64
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
EVIDENCIAS = AQUI.parent / "evidencias"
SAIDA = AQUI / "Cyber-Marca-dAgua.pdf"

NAVEGADORES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def figura(nome: str, legenda: str, faltando: list) -> str:
    arq = EVIDENCIAS / nome
    if not arq.exists() and arq.with_suffix(".jpg").exists():
        arq = arq.with_suffix(".jpg")
    if not arq.exists():
        faltando.append(f"print {nome}")
        return (f'<div class="pendente"><b>Print pendente:</b> salve como '
                f'<code>ciberseguranca/evidencias/{nome}</code> e rode o script de novo.<br>'
                f'{html.escape(legenda)}</div>')
    dados = base64.b64encode(arq.read_bytes()).decode()
    mime = "jpeg" if arq.suffix == ".jpg" else "png"
    return (f'<figure><img src="data:image/{mime};base64,{dados}" alt="{html.escape(legenda)}">'
            f'<figcaption>{html.escape(legenda)}</figcaption></figure>')


def texto_de(caminho: str) -> str:
    return f"<pre>{html.escape((RAIZ / caminho).read_text(encoding='utf-8').strip())}</pre>"


def montar() -> tuple[str, list]:
    faltando: list = []
    texto = (AQUI / "relatorio.html").read_text(encoding="utf-8")
    texto = re.sub(r"<!--IMG (.+?)\|(.+?)-->", lambda m: figura(m[1], m[2], faltando), texto)
    texto = re.sub(r"<!--TXT (.+?)-->", lambda m: texto_de(m[1]), texto)

    def decidir(m):
        faltando.append(f"decisão: {m[1]}")
        return f'<div class="pendente"><b>Decidir antes de enviar:</b> {m[1]}</div>'

    texto = re.sub(r"<!--DECIDIR (.+?)-->", decidir, texto)
    return texto, faltando


def achar_navegador() -> str:
    for caminho in NAVEGADORES:
        if Path(caminho).exists():
            return caminho
    achado = shutil.which("chrome") or shutil.which("msedge")
    if not achado:
        sys.exit("Não achei Chrome nem Edge. Instale um deles para gerar o PDF.")
    return achado


def main() -> None:
    texto, faltando = montar()
    temporario = AQUI / "_montado.html"
    temporario.write_text(texto, encoding="utf-8")
    try:
        subprocess.run(
            [achar_navegador(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={SAIDA}", temporario.as_uri()],
            check=True, capture_output=True, timeout=120,
        )
    finally:
        temporario.unlink(missing_ok=True)
    print(f"PDF gerado: {SAIDA}")
    if faltando:
        print("Pendências que ainda aparecem no PDF:")
        for item in faltando:
            print(f"  {item}")


if __name__ == "__main__":
    main()
