import aioconsole
from configs import *


class Menu:

    @staticmethod
    async def exibir_banner() -> None:
        """Exibe o banner do programa."""

        print(
            """
    ╔════════════════════════════════════════════╗
    ║         CONVERSOR TTS COMPLETO             ║
    ║ Text-to-Speech + Melhoria de Áudio em PT-BR║
    ╚════════════════════════════════════════════╝
    """
        )

    @staticmethod
    async def menu_principal() -> str:
        """Exibe o menu principal e retorna a opção escolhida."""
        await Menu.exibir_banner()
        print("\nEscolha uma opção:")
        print("1. 🚀 CONVERTER TEXTO PARA ÁUDIO")
        print("2. 🎙️ TESTAR VOZES")
        print("3. ⚡ MELHORAR ÁUDIO EXISTENTE")
        print("4. ❓ AJUDA")
        print("5. 🔄 ATUALIZAR")
        print("6. 🚪 SAIR")
        return await Menu.obter_opcao("\nOpção: ", ["1", "2", "3", "4", "5", "6"])

    @staticmethod
    async def obter_opcao(prompt: str, opcoes: list) -> str:
        """Solicita ao usuário uma entrada que esteja dentre as opções válidas."""
        while True:
            escolha = (await aioconsole.ainput(prompt)).strip()
            if escolha in opcoes:
                return escolha
            print("⚠️ Opção inválida! Tente novamente.")

    @staticmethod
    async def menu_vozes() -> str:
        """Exibe o menu de seleção de vozes e retorna a voz escolhida."""
        await Menu.exibir_banner()
        print("\nVozes disponíveis:")
        for i, voz in enumerate(VOZES_PT_BR, 1):
            print(f"{i}. {voz}")
        print(f"{len(VOZES_PT_BR) + 1}. Voltar")
        opcoes = [str(i) for i in range(1, len(VOZES_PT_BR) + 2)]
        escolha = await Menu.obter_opcao("\nEscolha uma voz: ", opcoes)
        if escolha == str(len(VOZES_PT_BR) + 1):
            return None
        return VOZES_PT_BR[int(escolha) - 1]
