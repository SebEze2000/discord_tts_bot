# 🤖 Discord TTS Bot (para Render)

Bot de Discord con gTTS + FFmpeg que reproduce mensajes y audios programados en un canal de voz.

## 🚀 Instrucciones

1. Subí este proyecto a GitHub.
2. En Render:
   - Crear nuevo **Web Service**.
   - Build Command:
     ```bash
     apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
     ```
   - Start Command:
     ```bash
     python bot.py
     ```
   - Agregar variable de entorno:
     ```
     TOKEN=tu_token_de_discord
     ```
3. Deployar y esperar que Render inicie el bot.
4. Verificá en el panel de Discord que el bot esté “En línea” ✅

## 🎧 Funcionalidad
- Conexión a canal de voz.
- Reproducción de audios MP3.
- TTS dinámico con el comando `!decir`.
- Anuncios automáticos a horarios definidos.
