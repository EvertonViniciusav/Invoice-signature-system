import os
import time
import shutil  # Para mover arquivos
import mysql.connector
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import xml.etree.ElementTree as ET

# Carregar variáveis do .env
load_dotenv()

# Conectar ao banco de dados
def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Pasta onde as notas fiscais serão salvas
PASTA_NOTAS = "C:\\notas_fiscais\\"
PASTA_LIDO = os.path.join(PASTA_NOTAS, "LIDO")

# Criar a pasta LIDO se não existir
if not os.path.exists(PASTA_LIDO):
    os.makedirs(PASTA_LIDO)

# Classe que monitora a pasta
class MonitorNotas(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        arquivo = event.src_path
        if arquivo.lower().endswith(".xml"):
            print(f"📄 Novo arquivo XML detectado: {arquivo}")
            processar_xml(arquivo)

# Função para processar o XML e salvar no banco
def processar_xml(caminho_arquivo):
    time.sleep(3)  # Espera para garantir que o arquivo foi completamente escrito

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as file:
            tree = ET.parse(file)
            root = tree.getroot()

        # Extrair informações do XML
        ns = {'ns': 'http://www.portalfiscal.inf.br/nfe'}
        numero_nota = root.find(".//ns:infNFe/ns:ide/ns:nNF", ns).text  # Número da NF
        chave_acesso = root.find(".//ns:protNFe/ns:infProt/ns:chNFe", ns).text  # Chave de acesso
        data_emissao = root.find(".//ns:infNFe/ns:ide/ns:dhEmi", ns).text[:10]  # Data de emissão
        empresa_id = 1  # Definir a empresa correta

        # Salvar no banco
        conn = conectar_banco()
        cursor = conn.cursor()
        sql = """
        INSERT INTO notas_fiscais (empresa_id, numero_nota, chave_acesso, data_emissao, caminho_arquivo)
        VALUES (%s, %s, %s, %s, %s)
        """
        valores = (empresa_id, numero_nota, chave_acesso, data_emissao, caminho_arquivo)
        cursor.execute(sql, valores)
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ Nota Fiscal {numero_nota} salva no banco com sucesso!")

        # Criar a pasta "LIDO" caso não exista
        pasta_lido = os.path.join(PASTA_NOTAS, "LIDO")
        os.makedirs(pasta_lido, exist_ok=True)

        # Mover o arquivo para a pasta "LIDO"
        destino = os.path.join(pasta_lido, os.path.basename(caminho_arquivo))
        time.sleep(2)  # Pequena pausa antes de mover para evitar erro de acesso
        shutil.move(caminho_arquivo, destino)

        print(f"📂 Arquivo movido para {destino}")

    except Exception as e:
        print(f"❌ Erro ao processar XML: {e}")

# Iniciar o monitoramento da pasta
def iniciar_monitoramento():
    event_handler = MonitorNotas()
    observer = Observer()
    observer.schedule(event_handler, PASTA_NOTAS, recursive=False)
    observer.start()
    print(f"🔍 Monitorando a pasta: {PASTA_NOTAS}")

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    iniciar_monitoramento()
