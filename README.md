# Gmail Notas Fiscais

Projeto em Python responsável por realizar integração com a API do Gmail para leitura automática de e-mails contendo notas fiscais, seja via:

* Anexo PDF
* Links externos de NFS-e/NF-e
* Portais de prefeitura
* Links dinâmicos de emissão de nota

O projeto realiza:

* Busca de e-mails no Gmail
* Filtragem por assunto relacionado a nota fiscal
* Download de anexos PDF
* Extração de texto de PDFs
* OCR utilizando Tesseract para PDFs escaneados/imagem
* Navegação automatizada com Selenium para notas enviadas via link
* Filtragem por Razão Social específica

---

# Objetivo Futuro

A ideia futura do projeto é integrar também com a API do Sienge para automatizar:

* leitura de notas fiscais
* conciliação
* validação
* processo de de/para
* automação financeira

---

# Estrutura do Projeto

```bash
.
├── main.py
├── helpers.py
├── extracao_nf_crawler.py
├── requirements.txt
├── .env.template
├── tabelas.xlsx
├── geckodriver
```

---

# Arquivos Principais

## `main.py`

Responsável pelo fluxo principal da aplicação:

* Busca e-mails na API do Gmail
* Processa PDFs
* Processa links externos
* Filtra Razão Social
* Gera relatório final

---

## `helpers.py`

Funções auxiliares:

* OCR
* Extração de texto
* Normalização
* Regex
* Processamento multipart de e-mails
* Conversão de PDF para imagem

---

## `extracao_nf_crawler.py`

Responsável por:

* Abrir links de notas fiscais
* Navegar via Selenium
* Realizar download automático de PDFs
* Esperar conclusão do download

---

## `tabelas.xlsx`

Arquivo que será utilizado futuramente para centralização das tabelas e regras de negócio do projeto.

---

# Requisitos

## Python

Recomendado:

```bash
Python 3.11+
```

---

# Instalação

## 1. Criar ambiente virtual

### Windows

```bash
python -m venv env
source env/Scripts/activate
```

### Linux/Mac

```bash
python3 -m venv env
source env/bin/activate
```

---

## 2. Instalar dependências

```bash
pip install -r requirements.txt
```

---

# Instalação do Tesseract OCR (OBRIGATÓRIO)

O projeto utiliza OCR para leitura de PDFs escaneados/imagem.

Baixe e instale o Tesseract OCR:

[Tesseract OCR Windows Installer](https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe?utm_source=chatgpt.com)

---

## Importante

Durante a instalação:

* Instale o idioma Português (`por`)
* Recomenda-se instalar no diretório padrão:

```bash
C:\Program Files\Tesseract-OCR\
```

---

## Configuração opcional do caminho do Tesseract

Caso necessário, descomente no `helpers.py`:

```python
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
```

---

# Configuração do Access Token Gmail

O projeto utiliza autenticação manual via Access Token da API do Gmail.

---

# Como gerar o Access Token

## 1. Acesse

[Google OAuth Playground](https://developers.google.com/oauthplayground/?utm_source=chatgpt.com)

---

## 2. Procure por:

```text
Gmail API v1
```

---

## 3. Selecione o scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

---

## 4. Clique em:

```text
Authorize APIs
```

---

## 5. Faça login com a conta organizacional

---

## 6. Permita o acesso

---

## 7. Clique em:

```text
Exchange authorization code for tokens
```

---

## 8. Copie o:

```text
access_token
```

---

# Configuração do `.env`

Copie o arquivo:

```bash
.env.template
```

para:

```bash
.env
```

---

## Exemplo

```env
ACCESS_TOKEN=SEU_TOKEN
```

---

# Configuração da Query Gmail

A busca de e-mails é feita utilizando a sintaxe nativa do Gmail.

Exemplo atual:

```python
QUERY = '''
    after:2026/05/15
    before:2026/05/16
    (NF OR "Nota Fiscal" OR NFS-e OR NFE OR Nota)
'''
```

---

# Tecnologias Utilizadas

* Python
* Gmail API
* Selenium
* Firefox WebDriver
* Tesseract OCR
* pytesseract
* pdfplumber
* pdf2image
* BeautifulSoup
* Requests

---

# Fluxo Geral da Aplicação

```text
Gmail API
    ↓
Busca de e-mails
    ↓
Filtro por assunto
    ↓
Extração HTML
    ↓
Extração de links
    ↓
Download PDFs
    ↓
OCR / leitura texto
    ↓
Filtro Razão Social
    ↓
Relatório final
```

---

# Observações

* O Access Token do Gmail expira periodicamente e deve ser renovado manualmente.
* O projeto utiliza Firefox + Geckodriver para automação Selenium.
* Alguns PDFs exigem OCR por serem imagens escaneadas.
* O projeto já possui fallback automático para OCR quando o PDF não contém texto legível.

---

# Melhorias Futuras

* Integração API Sienge
* Persistência em banco de dados
* Dashboard
* Processamento em lote
* Organização automática de notas
* OCR mais robusto
* Extração automática de CNPJ/valores
* Integração ERP
* Pipeline automatizado
* Dockerização
* Execução agendada

---
