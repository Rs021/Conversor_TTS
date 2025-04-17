import asyncio


class Help:
    async def exibir_ajuda() -> None:
        """Exibe o guia de ajuda do programa."""
        
        print(
            """
    📖 GUIA DE USO:

    1. CONVERSÃO DE TEXTO PARA ÁUDIO:
    • Prepare seu arquivo de texto (.txt) ou PDF (.pdf)
    • Escolha uma voz e aguarde a conversão
    • O áudio resultante pode ser melhorado na opção 3

    2. MELHORIA DE ÁUDIO:
    • Acelere arquivos de áudio/vídeo existentes
    • Escolha entre 0.5x e 2.0x de velocidade
    • Converta para MP3 (áudio) ou MP4 (vídeo com tela preta)
    • Arquivos longos são automaticamente divididos

    ⚠️ OBSERVAÇÕES:
    • Para arquivos muito grandes, o processo pode demorar
    • Certifique-se de ter espaço em disco suficiente
    • No Android/Termux, os arquivos são salvos em /storage/emulated/0/Download
    """
        )
        await aioconsole.ainput("\nPressione ENTER para voltar ao menu principal...")



