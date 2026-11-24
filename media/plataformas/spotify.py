import os
import tempfile
from yt_dlp import YoutubeDL

def baixar_spotify(url: str):
    """
    Lógica para baixar músicas do Spotify:
    1. O yt-dlp consegue extrair os metadados do link do Spotify.
    2. Ele busca automaticamente a melhor versão disponível (geralmente via YouTube).
    3. Converte para MP3.
    """
    temp_dir = tempfile.gettempdir()
    temp_base = f"spotify_{os.urandom(4).hex()}"
    
    # Configurações para buscar a música e converter para MP3
    ydl_opts = {
        'outtmpl': f'{temp_dir}/{temp_base}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
        # O yt-dlp usa o link do spotify para procurar no youtube automaticamente
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extrai a info e faz o download
            info = ydl.extract_info(url, download=True)
            
            # O arquivo final será .mp3 devido ao postprocessor
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + ".mp3"

            if not os.path.exists(filename):
                raise RuntimeError("O arquivo de áudio não foi gerado.")

            with open(filename, 'rb') as f:
                data = f.read()
            
            os.remove(filename) # Deleta o arquivo temporário
            return data, os.path.basename(filename)
            
    except Exception as e:
        print(f"Erro ao processar Spotify: {e}")
        raise ValueError(f"Não foi possível encontrar essa música do Spotify no YouTube.")
