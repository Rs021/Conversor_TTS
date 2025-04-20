# Conversor TTS (Text-to-Speech) – Texto para Fala em Português Brasileiro (PT-BR)

Um script simples e eficiente para converter textos em arquivos de áudio (MP3), utilizando a tecnologia **Edge TTS** da Microsoft. Compatível com  **Linux**, este projeto foi desenvolvido para facilitar a conversão de textos longos em áudio de alta qualidade.

---

## ✨ Funcionalidades

- ✅ **Compatível Linux**

- 🎙️ **Três vozes diferentes em português brasileiro**

- 📜 **Suporte a textos longos com divisão automática**

- 🔍 **Detecção automática de idioma e aviso se não for PT-BR**

- 🔢 **Conversão automática de números, ordinais e romanos para texto**

- 📄 **Conversão automática de arquivos PDF para texto**

- 📝 **Expansão de abreviações e símbolos especiais**

- ⏸️ **Pausa e retomada automática em caso de interrupção**

- 

---

## 🗂️ Suporte a Arquivos PDF



- **O script é capaz de detectar automaticamente se o arquivo selecionado é um PDF. Quando isso acontece, ele converte o conteúdo do PDF para .txt automaticamente, permitindo que o conteúdo seja lido pelo mecanismo TTS sem necessidade de ferramentas externas.**

- **PDFs escaneados (imagem) não são suportados.**

- **PDFs textuais (gerados por editores) funcionam normalmente.**

- **O arquivo .txt resultante é salvo automaticamente na mesma pasta**

# ⚙️ Passo a Passo de Instalação e Uso


## 🐧 Linux

### 1️⃣ Instalar Python e Git

No terminal, digite:

```bash
sudo apt update && sudo apt install python3 python3-pip git -y
```

### 2️⃣ Baixar o Script

```bash
curl -L -o Conversor_TTS.zip https://github.com/JonJonesBR/Conversor_TTS/archive/refs/heads/main.zip
```

### 3️⃣ Extrair o arquivo zipado para a pasta raiz do Termux

```bash
unzip -j Conversor_TTS.zip -d ~/
```

### 4️⃣ Instalar Dependências

```bash
sudo apt update -y && sudo apt upgrade -y
sudo apt install -y python git ffmpeg 
pip install edge-tts langdetect unidecode num2words chardet aioconsole PyMuPDF
```

### 5️⃣ Executar o Script

```bash
python pdf_tts_converter_to_mp4.py
```




## 📂 Como Funciona

-  **1.	Coloque seu arquivo (TXT ou PDF) na pasta Downloads.**

-  **2.	Execute o script.**

-  **3.	Escolha INICIAR no menu principal.**

-  **4.	Selecione o arquivo de texto.**

-  **5.	Escolha a voz.**

-  **6.	O áudio será criado na pasta Download.**

## 🎙️ Vozes Disponíveis

Thalita (voz otimizada neural)
Francisca	(voz alternativa suave)
Antonio	(voz clara e objetiva)

## 🛠️ Recursos Avançados

### 📜 Processamento inteligente de texto:

 •	Conversão de números: “123” vira “cento e vinte e três”

 •	Ordinais: “1º” vira “primeiro”

 •	Números romanos: “Capítulo IV” vira “Capítulo 4”

 •	Abreviações: “Dr.” vira “Doutor”

 •	Símbolos: “%” vira “porcento”, “&” vira “e”
	
### 🔄 Controle de conversão:

 •	Pausar e retomar (em caso de interrupção)

 •	Escolha entre um único arquivo ou múltiplos arquivos (um por parágrafo)

 •	Salvamento automático

## 📄 Conversão de PDF para TXT integrada

## ❓ Problemas Comuns e Soluções

- **Módulo não encontrado: Falta de dependência - Refaça o comando `pip install`.**
- **Áudio incompleto:	Interrupção durante conversão -	Rode novamente o script para continuar.**
- **❌ Se seu PDF conter notaçôes Latex, a conversão poderá falhar**

## 🔗 Links Úteis

- **Repositório Oficial	[Acessar](https://github.com/JonJonesBR/Conversor_TTS)**

- **Python	[Baixar](https://www.python.org/downloads/)**

## 📝 TODO

- **⌛ Suporte a Latex**
- **⬜ GUI** 


## 📄 Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Se você encontrou um bug, tem sugestões ou deseja ajudar no desenvolvimento, abra uma issue ou envie um pull request.

## ⭐ Se este projeto foi útil para você, deixe sua estrela no GitHub e ajude a divulgar! ⭐
