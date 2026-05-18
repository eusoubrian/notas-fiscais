import os
import time

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def download_nf(link_nfe):

    driver_path = os.path.join(
        os.getcwd(),
        'geckodriver'
    )

    download_path = os.path.abspath(
        os.getcwd()
    )

    # =====================================
    # ARQUIVOS EXISTENTES ANTES
    # =====================================

    arquivos_antes = set(
        os.listdir(download_path)
    )

    print('Iniciando service')

    firefox_service = Service(
        executable_path=driver_path
    )

    options = Options()

    options.set_preference(
        "browser.download.folderList",
        2
    )

    options.set_preference(
        "browser.download.manager.showWhenStarting",
        False
    )

    options.set_preference(
        "browser.download.dir",
        download_path
    )

    # PDF download automático
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/pdf"
    )

    # Não abrir visualizador PDF
    options.set_preference(
        "pdfjs.disabled",
        True
    )

    options.add_argument('--headless')

    driver = webdriver.Firefox(
        service=firefox_service,
        options=options
    )

    wait = WebDriverWait(driver, 20)

    print('Driver setado')

    driver.get(link_nfe)

    botao_download = wait.until(
        EC.element_to_be_clickable(
            (By.ID, 'btDownload')
        )
    )

    botao_download.click()

    print('Aguardando download finalizar...')

    # =====================================
    # ESPERA DOWNLOAD
    # =====================================

    timeout = 60
    inicio = time.time()

    arquivo_final = None

    while True:

        arquivos_depois = set(
            os.listdir(download_path)
        )

        novos_arquivos = (
            arquivos_depois - arquivos_antes
        )

        # PDFs baixados
        pdfs = [
            arq for arq in novos_arquivos
            if arq.lower().endswith('.pdf')
        ]

        # Downloads em andamento
        arquivos_part = [
            arq for arq in novos_arquivos
            if arq.lower().endswith('.part')
        ]

        # Se existe PDF e NÃO existe .part
        if pdfs and not arquivos_part:

            arquivo_final = os.path.join(
                download_path,
                pdfs[0]
            )

            break

        # timeout
        if time.time() - inicio > timeout:

            raise Exception(
                'Timeout esperando download PDF'
            )

        time.sleep(1)

    print(f'Download finalizado: {arquivo_final}')

    driver.quit()

    return arquivo_final