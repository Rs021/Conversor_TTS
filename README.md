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

- 💾 **Salvamento automático na pasta Download**

---

## 🗂️ Suporte a Arquivos PDF

#### 🚨 ATENÇÃO: CASO NA PRIMEIRA VEZ QUE TENTAR CONVERTER UM PDF PARA TXT DÊ UMA MENSAGEM DE ERRO, BASTA AGUARDAR O SCRIPT INSTALAR AUTOMATICAMENTE AS DEPENDÊNCIAS DESSA FUNÇÃO E, APÓS ISSO, SELECIONAR NOVAMENTE O ARQUIVO PDF A SER CONVERTIDO, QUE IRÁ FUNCIONAR! 😉

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

Baixe os arquivos do repositório:  

[Baixar Scripts](https://raw.github.com/JonJonesBR/Conversor_TTS/refs/heads/main/Conversor_TTS.zip)

Após isso, extraia os arquivos baixados em uma pasta de sua escolha e execute o terminal do windows nela com os seguintes possíveis passos:

Para **abrir o Terminal do Windows** (Windows Terminal ou Prompt de Comando) diretamente em uma pasta usando o **botão direito do mouse** ou um **atalho de teclado**, siga estas opções:

---

### **1. Adicionar "Abrir Terminal aqui" ao menu de contexto (botão direito)**
#### **Método 1: Usando o Windows Terminal (Recomendado)**
Se você tem o **Windows Terminal** instalado (padrão no Windows 11), ele já inclui a opção nativamente:
1. **Clique com o botão direito** em uma pasta ou no espaço vazio dentro dela.
2. Selecione **"Abrir no Terminal"** (ou **"Open in Terminal"** em inglês).

Se não aparecer, ative manualmente:
1. Abra o **Windows Terminal** como administrador.
2. Clique no **⬇ (menu suspenso)** > **Configurações**.
3. Vá em **"Configurações do Windows Terminal"** > **"Abrir o menu de contexto"**.
4. Ative **"Mostrar a entrada 'Abrir no Terminal' no menu de contexto de arquivos"**.

#### **Método 2: Adicionar manualmente via Registro (funciona para CMD/PowerShell)**
1. Pressione **`Win + R`**, digite **`regedit`** e pressione **Enter**.
2. Navegue até:
   ```
   HKEY_CLASSES_ROOT\Directory\Background\shell
   ```
3. **Clique direito** em **`shell`** > **Novo** > **Chave** e nomeie como **`Open Terminal Here`**.
4. Clique com o direito na nova chave, **Novo** > **Chave** e nomeie como **`command`**.
5. No lado direito, clique duas vezes em **`(Padrão)`** e insira um dos comandos abaixo:
   - **Windows Terminal**:
     ```
     wt -d "%V"
     ```
   - **PowerShell**:
     ```
     powershell.exe -NoExit -Command "Set-Location '%V'"
     ```
   - **CMD**:
     ```
     cmd.exe /k "cd /d "%V""
     ```
6. Reinicie o Explorer (via Gerenciador de Tarefas) ou o computador.

---

### **2. Atalho de teclado para abrir o Terminal em uma pasta**
1. Abra o **Explorador de Arquivos** e navegue até a pasta desejada.
2. Pressione **`Alt + D`** para focar na barra de endereço.
3. Digite **`wt`** (para Windows Terminal), **`powershell`** ou **`cmd`** e pressione **Enter**.
   - Isso abrirá o terminal no diretório atual.

#### **Atalho personalizado (se necessário)**:
- Crie um atalho na área de trabalho com o comando:
  ```cmd
  cmd /k "cd /d C:\caminho\da\pasta"
  ```
- Defina um atalho de teclado nas **Propriedades** do atalho.

---

### **Observações**:
- No **Windows 11**, a opção de terminal já vem integrada.
- Se usar **PowerShell 7+**, substitua `powershell.exe` por `pwsh.exe`.
- Para **WSL (Linux)**, use `wsl` no lugar de `cmd`.

Pronto! Agora você pode acessar o terminal rapidamente a partir de qualquer pasta. 🚀

### 3️⃣ Instalar Dependências

Abra o **Prompt de Comando** (Windows + R → `cmd`) e digite:

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git ffmpeg poppler termux-api
pip install edge-tts langdetect unidecode num2words chardet requests tqdm aioconsole
termux-setup-storage
pkg install unzip -y
```

### 4️⃣ Executar o Script

Navegue até a pasta onde salvou os scripts (ex.: Downloads) e execute o que preferir:

```bash
cd Downloads

python Conversor_TTS_com_MP4_09.04.2025.py
```

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
pkg update -y && pkg upgrade -y
pkg install -y python git ffmpeg poppler termux-api
pip install edge-tts langdetect unidecode num2words chardet requests tqdm aioconsole
termux-setup-storage
```

### 5️⃣ Executar o Script

```bash
python Conversor_TTS_com_MP4_09.04.2025.py
```

## 📱 Android (Termux)

### 1️⃣ Instalar Termux

Baixe a versão atualizada:

 •	[Termux no F-Droid](https://f-droid.org/packages/com.termux/)

 •	[Termux no GitHub](https://github.com/termux/termux-app/releases)

### 2️⃣ Preparar o Termux

Após abrir o Termux, rode:

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git ffmpeg poppler termux-api
pip install edge-tts langdetect unidecode num2words chardet requests tqdm aioconsole
termux-setup-storage
```

- **Se for perguhtado alguma coisa, basta digitar y no terminal e Enter**

### 3️⃣ Baixar o Script

```bash
curl -L -o Conversor_TTS.zip https://github.com/JonJonesBR/Conversor_TTS/archive/refs/heads/main.zip
```

### 4️⃣ Extrair o arquivo zipado para a pasta raiz do Termux

```bash
unzip -j Conversor_TTS.zip -d ~/
```

### 5️⃣ Executar o Script

```bash
python Conversor_TTS_com_MP4_09.04.2025.py
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
