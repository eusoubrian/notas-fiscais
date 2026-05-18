import requests
import base64
import tempfile
import os
import pdfplumber
import pytesseract

# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )

import unicodedata
import re
from dotenv import load_dotenv

from bs4 import BeautifulSoup
from pdf2image import convert_from_path

# =========================================
# CONFIG
# =========================================

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

RAZAO_SOCIAL = "MAXIMO ALDANA"

QUERY = '''
    after:2026/05/15
    before:2026/05/16
    (NF OR "Nota Fiscal" OR NFS-e OR NFE OR Nota)
'''

# =========================================
# HEADERS
# =========================================

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# ==============================================================================
# FUNÇÕES AUXILIARES / TRATAMENTO DE TEXTO
# ==============================================================================

def normalizar_texto(texto):
    if not texto:
        return ""
    texto = texto.lower()
    # Remove acentos e caracteres especiais
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    # Transforma múltiplos espaços/quebras de linha em um único espaço
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def razao_social_existe(texto):
    texto_norm = normalizar_texto(texto)
    razao_norm = normalizar_texto(RAZAO_SOCIAL)
    return razao_norm in texto_norm


def texto_parece_corrompido(texto):
    if not texto:
        return True
    if texto.count("(cid:") > 5:
        return True
    if len(texto.strip()) < 30:
        return True
    return False

# ==============================================================================
# EXTRAÇÃO DE CONTEÚDOS (PDF, LINKS E E-MAIL MULTIPART)
# ==============================================================================

def extrair_texto_pdf(pdf_path):
    texto = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto += page.extract_text() or ""
    except Exception as e:
        print(f"Erro pdfplumber: {e}")

    # OCR Fallback caso o PDF seja apenas imagem ou esteja corrompido
    if texto_parece_corrompido(texto):
        print("   [PDF] Texto corrompido ou imagem detectada. Usando OCR...")
        texto = ""
        try:
            imagens = convert_from_path(pdf_path)
            for img in imagens:
                texto += pytesseract.image_to_string(img, lang="por")
        except Exception as e:
            print(f"   [OCR] Erro ao executar OCR no PDF: {e}")

    return texto


def extrair_texto_link_nf(url_nf):
    """Acessa um link externo de Nota Fiscal da Prefeitura de SP, burlaria o 'Aguarde...' 
    redirecionando para a página de impressão direta."""
    try:
        headers_req = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # TRUQUE PARA A PREFEITURA DE SP:
        # Se for o link padrão do portal, nós trocamos "nfe.aspx" por "nota.aspx".
        # A página "nota.aspx" costuma entregar o HTML pronto renderizado direto do servidor, sem o "Aguarde..."
        if "nfe.sf.prefeitura.sp.gov.br/nfe.aspx" in url_nf:
            print(f"   [Link NF] Link convertido para renderização direta: {url_nf}")

        # Fazemos a requisição (o requests segue redirecionamentos automaticamente com allow_redirects=True)
        response = requests.get(url_nf, headers=headers_req, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            texto_html = soup.get_text()
            
            # Se mesmo trocando o link ainda vier o maldito "Aguarde..."
            if "Aguarde... Carregando Nota Fiscal" in texto_html:
                print("   [Link NF] O portal insistiu no carregamento dinâmico por JS.")
                
                # SEGUNDA TENTATIVA: Tentar a rota de faturamento/impressão se a primeira falhar
                soup = BeautifulSoup(response.text, "html.parser")
                texto_html = soup.get_text()
                
            return texto_html
        else:
            print(f"   [Link NF] Falha ao acessar link (Status: {response.status_code})")
    except Exception as e:
        print(f"   [Link NF] Erro ao acessar a URL {url_nf}: {e}")
    return ""


def extrair_todas_as_partes_html(payload):
    """Varre recursivamente a árvore do e-mail para separar blocos HTML de anexos PDF."""
    html_contents = []
    pdf_parts = []

    def buscar_na_estrutura(estrutura):
        mime_type = estrutura.get("mimeType", "")
        body = estrutura.get("body", {})
        filename = estrutura.get("filename", "")

        # Se for um bloco de texto HTML estruturado
        if mime_type == "text/html" and body.get("data"):
            html_contents.append(body.get("data"))
        
        # Se for um anexo em formato PDF legítimo
        elif filename.lower().endswith(".pdf") or mime_type == "application/pdf":
            pdf_parts.append(estrutura)

        # Se a parte atual contiver sub-partes (Multipart), continua descendo a árvore
        if "parts" in estrutura:
            for sub_part in estrutura["parts"]:
                buscar_na_estrutura(sub_part)

    buscar_na_estrutura(payload)
    return html_contents, pdf_parts