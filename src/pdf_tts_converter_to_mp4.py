import asyncio
from configs import *
from voiceTester import testVoice
from help import Help
from menu import Menu
from audio import Audio
import traceback
from textParser import ParserTxt


async def main() -> None:
    """Função principal do programa."""

    while True:
        opcao = await Menu.menu_principal()
        if opcao == "1":
            await ParserTxt.iniciar_conversao()
        elif opcao == "2":
            while True:
                voz_escolhida = await Audio.menu_vozes()
                if voz_escolhida is None:
                    break
                print(f"\n🎙️ Testando voz: {voz_escolhida}")
                await testVoice.testar_voz(voz_escolhida)
        elif opcao == "3":
            await Audio.menu_melhorar_audio()
        elif opcao == "4":
            await Help.exibir_ajuda()

        elif opcao == "6":
            print("\n👋 Obrigado por usar o Conversor TTS Completo!")
            break


1
if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido pelo usuário.")
    except:
        print(f"\n❌ Erro inesperado:")
        traceback.print_exc()
