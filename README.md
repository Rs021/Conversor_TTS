# Conversor TTS Lite – Texto para Fala em Português Brasileiro (PT-BR)

Um script simples e eficiente para converter textos em arquivos de áudio (MP3), utilizando a tecnologia **Edge TTS** da Microsoft. Compatível com **Windows**, **Linux** e **Android (via Termux)**, este projeto foi desenvolvido para facilitar a conversão de textos longos em áudio de alta qualidade.

---

## ✨ Funcionalidades

- ✅ **Compatível com Windows, Linux e Termux (Android)**

- 🎙️ **Três vozes diferentes em português brasileiro**

- 📜 **Suporte a textos longos com divisão automática**

- 🔍 **Detecção automática de idioma e aviso se não for PT-BR**

- 🔢 **Conversão automática de números, ordinais e romanos para texto**

- 📄 **Conversão automática de arquivos PDF para texto**

- 📝 **Expansão de abreviações e símbolos especiais**

- ⏸️ **Pausa e retomada automática em caso de interrupção**

- 📦 **Opção de gerar único arquivo ou separar por parágrafos**

- 💾 **Salvamento automático na pasta Downloads**

---

## 🗂️ Suporte a Arquivos PDF

- **O script é capaz de detectar automaticamente se o arquivo selecionado é um PDF. Quando isso acontece, ele converte o conteúdo do PDF para .txt automaticamente, permitindo que o conteúdo seja lido pelo mecanismo TTS sem necessidade de ferramentas externas.**

- **PDFs escaneados (imagem) não são suportados.**

- **PDFs textuais (gerados por editores) funcionam normalmente.**

- **O arquivo .txt resultante é salvo automaticamente na mesma pasta**

# ⚙️ Passo a Passo de Instalação e Uso

## 🪟 Windows

### 1️⃣ Instalar Python

Baixe e instale o Python (3.6 ou superior):  
[Download Python](https://www.python.org/downloads/)

### 2️⃣ Baixar o Script

Baixe o arquivo `conversor_tts_lite.py` do repositório:  

[Baixar Script](https://github.com/JonJonesBR/Conversor_TTS)

### 3️⃣ Instalar Dependências

Abra o **Prompt de Comando** (Windows + R → `cmd`) e digite:

```bash
pip install edge-tts langdetect unidecode num2words chardet requests
```

### 4️⃣ Executar o Script

Navegue até a pasta onde salvou o script (ex.: Downloads):

```bash
cd Downloads

python conversor_tts_lite.py
```

## 🐧 Linux

### 1️⃣ Instalar Python e Git

No terminal, digite:

```bash
sudo apt update && sudo apt install python3 python3-pip git -y
```

### 2️⃣ Baixar o Script

```bash
curl -o conversor_tts_lite.py https://raw.githubusercontent.com/JonJonesBR/Conversor_TTS/main/conversor_tts_lite.py
```

### 3️⃣ Instalar Dependências

```bash
pip3 install edge-tts langdetect unidecode num2words chardet requests
```

### 4️⃣ Executar o Script

```bash
python3 conversor_tts_lite.py
```

## 📱 Android (Termux)

### 1️⃣ Instalar Termux

Baixe a versão atualizada:

 •	[Termux no F-Droid](https://f-droid.org/packages/com.termux/)

 •	[Termux no GitHub](https://github.com/termux/termux-app/releases)

### 2️⃣ Preparar o Termux

Após abrir o Termux, rode:

```bash
termux-setup-storage
apt update && apt upgrade -y
apt install python git -y
```
- **Se for perguhtado alguma coisa, basta digitar y no terminal e Enter**

### 3️⃣ Baixar o Script

```bash
curl -o conversor_tts_lite.py https://raw.githubusercontent.com/JonJonesBR/Conversor_TTS/main/conversor_tts_lite.py
```

### 4️⃣ Instalar Dependências

```bash
pip install edge-tts langdetect unidecode num2words chardet requests
```

### 5️⃣ Executar o Script

```bash
python conversor_tts_lite.py
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

- **Arquivo não encontrado: Caminho errado ou permissão -	No Termux, execute: `termux-setup-storage`.**

- **Áudio incompleto:	Interrupção durante conversão -	Rode novamente o script para continuar.**

## 🔗 Links Úteis

- **Repositório Oficial	[Acessar](https://github.com/JonJonesBR/Conversor_TTS)**

- **Python para Windows	[Baixar](https://www.python.org/downloads/)**

- **Termux (F-Droid)	[Baixar](https://f-droid.org/packages/com.termux/)**

- **Termux (GitHub)	[Baixar](https://github.com/termux/termux-app/releases)**

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Se você encontrou um bug, tem sugestões ou deseja ajudar no desenvolvimento, abra uma issue ou envie um pull request.

## ⭐ Se este projeto foi útil para você, deixe sua estrela no GitHub e ajude a divulgar! ⭐