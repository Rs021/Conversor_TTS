import edge_tts
import asyncio

class testVoice:

    @staticmethod
    async def testar_voz(voz: str) -> None:
        """
        Testa uma voz específica com um texto de exemplo e salva a amostra
        em uma pasta na pasta Download do Android. Após a geração, retorna automaticamente.
        """
        texto_teste = "Apenas um teste simples"
        communicate = edge_tts.Communicate(texto_teste, voz)

        file_path = "teste_voz.mp3"

        try:
            await communicate.save(file_path)
            print(f"\n✅ Arquivo de teste gerado: {file_path}")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"\n❌ Erro ao testar voz: {str(e)}")