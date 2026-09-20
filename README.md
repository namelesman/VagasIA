# VagasIA 🚀

VagasIA é uma automação inteligente em Python projetada para facilitar e agilizar o processo de candidatura a vagas de emprego. Utilizando a API do Google Gemini (Visão Computacional e Geração de Texto), a ferramenta processa imagens de anúncios de vagas (como prints do LinkedIn, Instagram, etc.), extrai as informações da vaga e do recrutador, redige um e-mail de apresentação personalizado de acordo com o idioma da vaga (PT, EN ou ES) e envia automaticamente o e-mail via Gmail com o currículo correto em anexo.

## Funcionalidades ✨

- **Extração via Imagem (OCR + IA):** Lê imagens de vagas colocadas na pasta `vagas_nao_aplicadas/` e extrai o e-mail, título da vaga, nome da empresa, requisitos e idioma sugerido.
- **Geração de E-mail Personalizado:** Cria uma carta de apresentação única (usando o Gemini 3.6 Flash) destacando sua experiência alinhada aos requisitos encontrados na vaga.
- **Suporte Multi-idioma:** O e-mail e o currículo anexado se adaptam automaticamente ao idioma detectado na vaga (Português, Inglês ou Espanhol).
- **Envio Automático via SMTP:** Autentica no Gmail via senha de aplicativo (App Password) e envia o e-mail de candidatura em seu nome.
- **Organização de Histórico:** Move a vaga processada para a pasta `Vagas_Aplicadas/` criando um registro com os dados extraídos e o e-mail enviado.

## Tecnologias 🛠️

- **Python 3**
- **Google GenAI (Gemini)** para visão e processamento de linguagem natural
- **Pillow (PIL)** para manipulação de imagens
- **smtplib / email.message** para envio de e-mails
- **python-dotenv** para gerenciamento de variáveis de ambiente

## Como Usar ⚙️

1. Renomeie o arquivo `.env.example` para `.env` e preencha com seus dados (API Key do Gemini, E-mail do Gmail, App Password, caminhos para os PDFs dos seus currículos).
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Jogue as capturas de tela das vagas na pasta `vagas_nao_aplicadas/`.
4. Execute o script:
   ```bash
   python main.py
   ```
5. O script irá analisar as imagens, enviar as candidaturas e mover os arquivos processados para `Vagas_Aplicadas/`.
