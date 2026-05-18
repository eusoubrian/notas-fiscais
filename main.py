import requests
import base64
import tempfile
import os

from extracao_nf_crawler import *
from helpers import *

# ==============================================================================
# FLUXO PRINCIPAL DE EXECUÇÃO
# ==============================================================================

def main():
    url_lista = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    params = {"q": QUERY}

    print("Buscando e-mails no Gmail...")
    response = requests.get(url_lista, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"Erro na requisição inicial: {response.json()}")
        return

    emails = response.json().get("messages", [])
    print(f"Emails encontrados com a busca: {len(emails)}")

    emails_validos = []

    for email_item in emails:
        message_id = email_item["id"]
        print(f"\n----------------------------------------\nProcessando e-mail: {message_id}")

        detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}"
        detail_response = requests.get(detail_url, headers=HEADERS)
        
        if detail_response.status_code != 200:
            print(f"Não foi possível obter detalhes do e-mail {message_id}")
            continue

        msg = detail_response.json()
        payload = msg.get("payload", {})
        headers_email = payload.get("headers", [])

        # Extrai o Assunto (Subject) do e-mail
        assunto = next((h["value"] for h in headers_email if h["name"] == "Subject"), "(Sem Assunto)")

        encontrou_razao = False
        links_email = []

        # Separa dinamicamente textos HTML e PDFs, ignorando inline PNGs de assinatura
        dados_html, partes_pdf = extrair_todas_as_partes_html(payload)

        # 1. Analisa os corpos em HTML do e-mail
        for data_base64 in dados_html:
            try:
                html = base64.urlsafe_b64decode(data_base64).decode(errors="ignore")
                soup = BeautifulSoup(html, "html.parser")

                # Alimenta a lista de links para checagem posterior de portais externos
                for a in soup.find_all("a", href=True):
                    links_email.append(a["href"])
            except Exception as e:
                print(f"Erro ao decodificar HTML de uma das partes: {e}")

        # 2. Analisa os anexos em PDF (se houver e se ainda não validou a Razão Social)
        for part in partes_pdf:
            if encontrou_razao:
                break  # Se já validou no texto, pula processamento pesado de PDF

            body = part.get("body", {})
            attachment_id = body.get("attachmentId")

            if attachment_id:
                print(f"-> Baixando anexo PDF: {part.get('filename')}")
                numero_nota_fiscal = part.get('filename').replace('.pdf', '').rsplit('_')[-1]
                attach_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/attachments/{attachment_id}"
                attach_response = requests.get(attach_url, headers=HEADERS)
                attach_data = attach_response.json()
                
                if "data" in attach_data:
                    file_data = attach_data["data"]
                    pdf_bytes = base64.urlsafe_b64decode(file_data)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                        temp_pdf.write(pdf_bytes)
                        temp_path = temp_pdf.name

                    texto_pdf = extrair_texto_pdf(temp_path)
                    os.remove(temp_path)

                    if razao_social_existe(texto_pdf):
                        print("   Razão social encontrada no conteúdo do PDF!")
                        encontrou_razao = True

        # 3. Analisa links de NF externos (caso não tenha achado no corpo do e-mail e nem no PDF)
        if not encontrou_razao and links_email:
            for link in links_email:
                # Alvos comuns de links de NFS-e (Prefeitura de SP, links genéricos de aspx/notafiscal)
                if "nfe.sf.prefeitura.sp.gov.br" in link or "nfe.aspx" in link or "notafiscal" in link.lower():
                    print(f"-> Verificando link de NF externo: {link}")
                    nf_path = download_nf(link)
                    nf_arquivo = os.path.basename(nf_path)
                    numero_nota_fiscal = (
                        nf_arquivo
                        .replace('.pdf', '')
                        .rsplit('_', 1)[-1]
                    )

                    texto_link_nf = extrair_texto_pdf(nf_path)
                    
                    if razao_social_existe(texto_link_nf):
                        print("   Razão social encontrada dentro da página da NF externa!")
                        encontrou_razao = True
                        break  # Já achou a correspondência, pode parar de olhar os outros links

        # Se passar em qualquer um dos filtros, salva na lista de interesses
        if encontrou_razao:
            email_link_direto = f"https://mail.google.com/mail/u/0/#inbox/{message_id}"
            emails_validos.append({
                "assunto": assunto,
                "numero_nota_fiscal": numero_nota_fiscal,
                "email_link": email_link_direto,
                "links": list(set(links_email))  # Remove duplicados usando set
            })

    # ==============================================================================
    # EXIBIÇÃO DO RELATÓRIO FINAL
    # ==============================================================================
    print("\n" + "="*40)
    print("           EMAILS FILTRADOS VÁLIDOS")
    print("="*40)

    if not emails_validos:
        print("Nenhum e-mail correspondeu aos critérios da Razão Social informada.")
    else:
        for item in emails_validos:
            print(f"\nASSUNTO: {item['assunto']}")
            print(f"LINK DIRETO: {item['email_link']}")
            if item["links"]:
                print("LINKS DETECTADOS NO CORPO:")
                for link in item["links"]:
                    print(f"  - {link}")
    print("\n" + "="*40)

if __name__ == "_main_":
    main()