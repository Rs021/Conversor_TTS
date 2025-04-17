import os
import asyncio
import time
import aioconsole
from configs import *
from formatText import textFormat
from voiceTester import testVoice
from help import Help
from menu import Menu
from files_utils import filesUtils
from audio import Audio
from pdfParser import pdfCoverter
# Just for test














# ================== FUNÇÕES DE LEITURA E PROCESSAMENTO DE ARQUIVOS ==================










# ================== FUNÇÕES DE CONVERSÃO TTS ==================


async def iniciar_conversao() -> None:
    """
    Inicia o processo de conversão de texto para áudio de forma concorrente.
    O tamanho dos chunks é calculado dinamicamente.
    """
    global CANCELAR_PROCESSAMENTO
    CANCELAR_PROCESSAMENTO = False

    try:
        caminho_arquivo = await pdfCoverter.selecionar_arquivo()
        if not caminho_arquivo or CANCELAR_PROCESSAMENTO:
            return

        voz_escolhida = await Menu.menu_vozes()
        if voz_escolhida is None or CANCELAR_PROCESSAMENTO:
            return

        print("\n📖 Lendo arquivo...")
        texto = filesUtils.ler_arquivo_texto(caminho_arquivo)
        if not texto or CANCELAR_PROCESSAMENTO:
            print("\n❌ Arquivo vazio ou ilegível")
            await asyncio.sleep(2)
            return

        print("🔄 Processando texto...")
        texto_processado = textFormat.processar_texto(texto)

        partes = textFormat.dividir_texto(texto_processado)
        total_partes = len(partes)
        print(f"\n📊 Texto dividido em {total_partes} parte(s).")
        print("Para interromper a conversão a qualquer momento, pressione CTRL + C.\n")

        nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
        nome_base = filesUtils.limpar_nome_arquivo(nome_base)
        diretorio_saida = os.path.join(
            os.path.dirname(caminho_arquivo), f"{nome_base}_audio"
        )

        if not os.path.exists(diretorio_saida):
            os.makedirs(diretorio_saida)

        temp_files = []
        start_time = time.time()
        semaphore = asyncio.Semaphore(5)  # Limite de 5 tarefas simultâneas

        async def processar_chunk(i, parte):
            async with semaphore:
                if CANCELAR_PROCESSAMENTO:
                    return None

                saida_temp = os.path.join(
                    diretorio_saida, f"{nome_base}_temp_{i:03d}.mp3"
                )
                temp_files.append(saida_temp)

                tentativa = 1
                while tentativa <= MAX_TENTATIVAS:
                    if CANCELAR_PROCESSAMENTO:
                        return None

                    inicio_chunk = time.time()
                    sucesso = await Audio.converter_texto_para_audio(
                        parte, voz_escolhida, saida_temp
                    )

                    if sucesso:
                        tempo_chunk = time.time() - inicio_chunk
                        print(
                            f"✅ Parte {i}/{total_partes} | Tentativa {tentativa}/{MAX_TENTATIVAS} | Tempo: {tempo_chunk:.1f}s"
                        )
                        return True
                    else:
                        print(
                            f"🔄 Tentativa {tentativa}/{MAX_TENTATIVAS} falhou para parte {i}. Reiniciando..."
                        )
                        tentativa += 1
                        await asyncio.sleep(2)  # Intervalo entre tentativas

                print(
                    f"❌ Falha definitiva na parte {i} após {MAX_TENTATIVAS} tentativas"
                )
                return False

        tasks = [processar_chunk(i + 1, p) for i, p in enumerate(partes)]
        results = await asyncio.gather(*tasks)

        # Verificar se todas as partes foram convertidas
        if not all(results):
            print("\n⚠️ Algumas partes falharam. Não é possível unificar.")
            return

        if not CANCELAR_PROCESSAMENTO and any(results):
            print("\n🔄 Unificando arquivos...")
            arquivo_final = os.path.join(diretorio_saida, f"{nome_base}.mp3")

            if Audio.unificar_audio(temp_files, arquivo_final):
                for f in temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                overall_time = time.time() - start_time
                print(
                    f"\n🎉 Conversão concluída em {overall_time:.1f} s! Arquivo final: {arquivo_final}"
                )

                # Pergunta se deseja melhorar o áudio
                melhorar = (
                    (
                        await aioconsole.ainput(
                            "\nDeseja melhorar o áudio gerado (ajustar velocidade)? (s/n): "
                        )
                    )
                    .strip()
                    .lower()
                )
                if melhorar == "s":
                    await Audio.processar_melhorar_audio(arquivo_final)
            else:
                print("\n❌ Falha na unificação dos arquivos.")

        await aioconsole.ainput("\nPressione ENTER para continuar...")

    except asyncio.CancelledError:
        print("\n🚫 Operação cancelada pelo usuário")
    finally:
        CANCELAR_PROCESSAMENTO = True
        if "temp_files" in locals():
            for f in temp_files:
                if os.path.exists(f):
                    os.remove(f)
        await asyncio.sleep(1)


async def main() -> None:
    """Função principal do programa."""

    while True:
        opcao = await Menu.menu_principal()
        if opcao == "1":
            await iniciar_conversao()
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
