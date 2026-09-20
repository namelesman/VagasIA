import os
import sys
import glob
import shutil
import re
import time
import smtplib
from email.message import EmailMessage
import mimetypes

from google import genai
from google.genai import errors
from PIL import Image
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# ---------------------------------------------------------
# CARREGAR CONFIGURAÇÕES SEGURAS
# ---------------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_REMETENTE = os.getenv("GMAIL_EMAIL")
SENHA_APP_GMAIL = os.getenv("GMAIL_APP_PASSWORD")

NOME_CANDIDATO = os.getenv("NOME_CANDIDATO", "Thiago Santos Medeiros")
LINKEDIN = os.getenv("LINKEDIN")
PORTFOLIO = os.getenv("PORTFOLIO")

CURRICULO_PT = os.getenv("CURRICULO_PT")
CURRICULO_EN = os.getenv("CURRICULO_EN")
CURRICULO_ES = os.getenv("CURRICULO_ES")

if not API_KEY or not EMAIL_REMETENTE:
    print("❌ Erro Crítico: O arquivo .env não foi configurado corretamente.")
    print("Por favor, renomeie o arquivo .env.example para .env e preencha seus dados.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def sanitizar_nome_pasta(texto):
    """
    Remove caracteres perigosos e impede ataques de Path Traversal (ex: ../../)
    """
    texto_limpo = re.sub(r'[\\/*?:"<>|.\n\r]', "", texto)
    return texto_limpo.strip()

def extrair_campo(texto, campo):
    match = re.search(fr"^{campo}:\s*(.+)$", texto, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Não encontrado"

def gerar_com_retry(prompt, img=None, retentativas=4):
    for i in range(retentativas):
        try:
            if img:
                return client.models.generate_content(model='gemini-3.6-flash', contents=[prompt, img])
            else:
                return client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
        except errors.ServerError as e:
            if i < retentativas - 1:
                espera = 10
                print(f"   [⏳ Google Ocupado] Tentando de novo em {espera}s... (Tentativa {i+1} de {retentativas})")
                time.sleep(espera)
            else:
                raise e

def analisar_vaga(caminho_imagem):
    print(f"Processando a imagem da vaga: {caminho_imagem}...")
    try:
        img = Image.open(caminho_imagem)
    except FileNotFoundError:
        return None

    # Prompt protegido pedindo formato estrito
    prompt = """
    Você é um assistente de recrutamento de software. 
    Analise esta imagem de uma vaga de emprego.
    Extraia as informações e retorne EXATAMENTE neste formato de texto simples:
    
    Email: [email encontrado na imagem, ou 'Não encontrado']
    Vaga: [titulo da vaga]
    Empresa: [nome da empresa, ou 'Desconhecida']
    Requisitos: [lista resumida de requisitos]
    Idioma: [PT-BR para português, EN-US para inglês, ES-ES para espanhol]
    """

    response = gerar_com_retry(prompt, img=img)
    resultado = response.text.strip()
    
    print("\n--- Resultado da Visão Computacional ---")
    print(resultado)
    print("----------------------------------------\n")
    return resultado

def gerar_email(dados_vaga):
    print("Gerando texto do e-mail de candidatura baseado nos requisitos...")
    prompt_email = f"""
    Abaixo estão os dados de uma vaga:
    {dados_vaga}
    
    Sua missão é escrever o corpo de um e-mail de candidatura profesional e direto.
    Regras:
    1. O candidato se chama {NOME_CANDIDATO}.
    2. Resumo da experiência do candidato:
       - Desenvolvedor Full Stack com foco em React, Next.js, Node.js, NestJS e Python.
       - Experiência profissional na 'Hollow Soft' desenvolvendo APIs RESTful e interfaces responsivas.
       - Experiência prévia na Prefeitura de Jaboatão dos Guararapes.
       - Cursando Ciência da Computação na UNIFBV e possui o curso CS50 de Harvard.
       - Bancos de dados: PostgreSQL, MongoDB, SQL.
    3. SE a vaga (Idioma) for PT-BR, escreva o e-mail em português.
    4. SE a vaga (Idioma) for EN-US, escreva o e-mail em inglês.
    5. SE a vaga (Idioma) for ES-ES (Espanhol), escreva o e-mail em espanhol.
    6. Mostre entusiasmo, relacione a experiência com a vaga e diga que o currículo está em anexo. Não coloque "Assunto" no texto.
    7. Na assinatura, coloque:
       Portfólio: {PORTFOLIO}
       LinkedIn: {LINKEDIN}
    """
    response = gerar_com_retry(prompt_email)
    return response.text.strip()

def enviar_email_smtp(dados, corpo_email):
    email_destino = extrair_campo(dados, "Email")
    if "não encontrado" in email_destino.lower():
        print("⚠️ E-mail não detectado na imagem. O envio automático foi cancelado.")
        return False
        
    vaga = extrair_campo(dados, "Vaga")
    idioma = extrair_campo(dados, "Idioma")
    
    print(f"📧 Preparando envio real para: {email_destino}...")
    
    if "PT-BR" in idioma.upper():
        anexo = CURRICULO_PT
        assunto = f"Candidatura - {vaga} - {NOME_CANDIDATO}"
    elif "ES-ES" in idioma.upper():
        anexo = CURRICULO_ES
        assunto = f"Candidatura - {vaga} - {NOME_CANDIDATO}"
    else:
        anexo = CURRICULO_EN
        assunto = f"Job Application - {vaga} - {NOME_CANDIDATO}"
        
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = email_destino
    msg.set_content(corpo_email)
    
    try:
        ctype, encoding = mimetypes.guess_type(anexo)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        
        with open(anexo, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(anexo))
    except Exception as e:
        print(f"❌ Erro ao anexar currículo ({anexo}): {e}")
        return False

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP_GMAIL)
            smtp.send_message(msg)
        print(f"✅ SUCESSO! E-mail enviado oficialmente para {email_destino}!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ FALHA NO LOGIN: Verifique sua Senha de Aplicativo do Gmail no arquivo .env")
        return False
    except Exception as e:
        print(f"❌ Erro de conexão SMTP: {e}")
        return False

def organizar_arquivos(imagem_original, dados, corpo_email):
    empresa = extrair_campo(dados, "Empresa")
    vaga = extrair_campo(dados, "Vaga")
    
    # Sanitização segura de diretório (Vulnerabilidade corrigida)
    nome_pasta = sanitizar_nome_pasta(f"{vaga} - {empresa}")
    nome_img = sanitizar_nome_pasta(empresa)
    
    # Prevenção extra caso a IA retorne vazio e a sanitização zere a string
    if not nome_pasta:
        nome_pasta = f"Vaga_{int(time.time())}"
    if not nome_img:
        nome_img = f"Img_{int(time.time())}"
        
    pasta_destino = os.path.join("Vagas_Aplicadas", nome_pasta)
    os.makedirs(pasta_destino, exist_ok=True)
    
    extensao = os.path.splitext(imagem_original)[1]
    caminho_nova_img = os.path.join(pasta_destino, f"{nome_img}{extensao}")
    caminho_txt = os.path.join(pasta_destino, "email.txt")
    
    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write("=== DADOS EXTRAÍDOS ===\n" + dados + "\n\n=== E-MAIL GERADO ===\n" + corpo_email)
        
    shutil.move(imagem_original, caminho_nova_img)

if __name__ == "__main__":
    pasta_entrada = "vagas_nao_aplicadas"
    os.makedirs(pasta_entrada, exist_ok=True)
    
    imagens_para_processar = glob.glob(os.path.join(pasta_entrada, "*.jpg")) + \
                             glob.glob(os.path.join(pasta_entrada, "*.png")) + \
                             glob.glob(os.path.join(pasta_entrada, "*.jpeg"))
    
    if not imagens_para_processar:
        print(f"⚠️ Nenhuma imagem encontrada na pasta '{pasta_entrada}'.")
        sys.exit(0)
        
    for index, caminho_img in enumerate(imagens_para_processar):
        print(f"\n{"="*50}")
        print(f"📝 VAGA {index + 1}/{len(imagens_para_processar)}: {os.path.basename(caminho_img)}")
        print(f"{"="*50}")
        
        dados = analisar_vaga(caminho_img)
        if dados:
            time.sleep(3) 
            corpo_email = gerar_email(dados)
            
            # ATENÇÃO: Tenta enviar o e-mail de verdade!
            enviado = enviar_email_smtp(dados, corpo_email)
            
            # Organiza a pasta independente se enviou ou não (fica como rascunho)
            organizar_arquivos(caminho_img, dados, corpo_email)
            
    print("\n✅ Lote processado com sucesso!")
