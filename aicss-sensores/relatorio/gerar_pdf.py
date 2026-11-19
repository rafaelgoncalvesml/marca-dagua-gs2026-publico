"""Gera o PDF do AICSS a partir de relatorio.html.

Uso: python gerar_pdf.py

Lê os prints de ../evidencias/ pelo nome. Print que ainda não existe vira uma caixa
amarela com o nome do arquivo esperado: salve o print com esse nome e rode de novo.
Precisa do Chrome ou do Edge instalado (impressão headless em PDF).
"""
import base64
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
EVIDENCIAS = AQUI.parent / "evidencias"
SAIDA = AQUI / "AICSS-Marca-dAgua.pdf"

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
        faltando.append(nome)
        return (f'<div class="pendente"><b>Print pendente:</b> salve como '
                f'<code>aicss-sensores/evidencias/{nome}</code> e rode o script de novo.<br>'
                f'{html.escape(legenda)}</div>')
    dados = base64.b64encode(arq.read_bytes()).decode()
    mime = "jpeg" if arq.suffix == ".jpg" else "png"
    return (f'<figure><img src="data:image/{mime};base64,{dados}" alt="{html.escape(legenda)}">'
            f'<figcaption>{html.escape(legenda)}</figcaption></figure>')


def json_bruto(nome: str) -> str:
    texto = (EVIDENCIAS / nome).read_text(encoding="utf-8").strip()
    try:
        texto = json.dumps(json.loads(texto), ensure_ascii=False)
    except ValueError:
        pass
    return f"<pre>{html.escape(texto)}</pre>"


def codigo(caminho: str) -> str:
    texto = (RAIZ / caminho).read_text(encoding="utf-8")
    return f'<pre class="fonte">{html.escape(texto)}</pre>'


def montar() -> tuple[str, list]:
    faltando: list = []
    texto = (AQUI / "relatorio.html").read_text(encoding="utf-8")
    texto = re.sub(r"<!--IMG (.+?)\|(.+?)-->", lambda m: figura(m[1], m[2], faltando), texto)
    texto = re.sub(r"<!--JSON (.+?)-->", lambda m: json_bruto(m[1]), texto)
    texto = re.sub(r"<!--CODE (.+?)-->", lambda m: codigo(m[1]), texto)
    return texto, faltando


def achar_navegador() -> str:
    for caminho in NAVEGADORES:
        if Path(caminho).exists():
            return caminho
    achado = shutil.which("chrome") or shutil.which("msedge")
    if not achado:
        sys.exit("Não achei Chrome nem Edge. Instale um deles para gerar o PDF.")
    return achado


def neutraliza_metadados(pdf: Path) -> None:
    """Troca Creator e Producer (user agent do Chrome, Skia) por texto neutro do mesmo tamanho,
    para o arquivo não carregar rastro de ferramenta e as posições do PDF continuarem válidas."""
    dados = pdf.read_bytes()
    for chave, texto in ((b"/Creator", b"Marca d'Agua"), (b"/Producer", b"Marca d'Agua")):
        m = re.search(chave + rb"\s*\(((?:[^()\\]|\\.)*)\)", dados)
        if m:
            tam = len(m.group(1))
            novo = texto[:tam].ljust(tam, b" ")
            dados = dados[:m.start(1)] + novo + dados[m.end(1):]
    pdf.write_bytes(dados)


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
    neutraliza_metadados(SAIDA)
    print(f"PDF gerado: {SAIDA}")
    if faltando:
        print("Prints que faltam:")
        for nome in faltando:
            print(f"  {nome}")


if __name__ == "__main__":
    main()
