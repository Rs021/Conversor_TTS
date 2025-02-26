# Conversor TTS (Text-to-Speech)

Um conversor de texto para áudio em português brasileiro, utilizando a tecnologia Edge TTS. Este script oferece uma interface amigável e recursos avançados para converter textos em arquivos de áudio com qualidade profissional.

## ✨ Características

- 🎯 Interface intuitiva e amigável
- 🗣️ Três vozes diferentes em português brasileiro
- 📝 Suporte a textos longos
- 🔍 Detecção automática de idioma
- 🔄 Conversão automática de números para texto
- 📊 Otimização para melhor pronúncia
- ⏸️ Possibilidade de pausar e retomar conversões

## 📋 Pré-requisitos

- Python 3.6 ou superior
- Conexão com a internet
- Pip (gerenciador de pacotes Python)

## 🚀 Instalação

1. Clone este repositório:
```bash
git clone https://github.com/[seu-usuario]/conversor-tts.git
cd conversor-tts
```

2. Instale as dependências necessárias:
```bash
pip install edge-tts langdetect unidecode num2words
```

## 💻 Como Usar

1. Execute o script:
```bash
python conversor_tts_lite.py
```

2. No menu principal, você terá as seguintes opções:
   - 🚀 **INICIAR**: Começa o processo de conversão
   - 🎙️ **VOZES**: Escolha entre as vozes disponíveis
   - ❓ **AJUDA**: Exibe o guia de uso
   - 🚪 **SAIR**: Encerra o programa

3. Para converter um texto:
   - Salve seu texto em um arquivo .txt
   - Selecione a opção "INICIAR"
   - Escolha o arquivo de texto
   - Selecione a voz desejada
   - Aguarde a conversão

## 🎙️ Vozes Disponíveis

- **Thalita** (padrão) - Otimizada para múltiplos idiomas
- **Francisca** - Voz feminina alternativa
- **Antonio** - Voz masculina

## 🛠️ Recursos Avançados

### Conversão Automática
- Números ordinais (1º → primeiro)
- Números romanos (Cap. IV → Capítulo 4)
- Abreviações (Dr. → Doutor)
- Símbolos especiais (% → porcento)

### Controle de Conversão
- Use Ctrl+C para pausar/interromper
- Opção de manter arquivos separados ou unificados
- Retomada de conversões interrompidas

## ⚠️ Observações

- O arquivo de áudio será salvo na mesma pasta do arquivo de texto
- O nome do arquivo de áudio será baseado na primeira linha do texto
- É necessária conexão com a internet para a conversão

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no GitHub!