import os
import sys
import re
import asyncio
from datetime import datetime, time
from pathlib import Path
from typing import Optional

# --- Parche para Python 3.13 (audioop eliminado) ---
import importlib, sys

try:
    audioop = importlib.import_module("audioop_lts.audioop_lts")
except ModuleNotFoundError:
    try:
        audioop = importlib.import_module("audioop_lts")
    except ModuleNotFoundError:
        print("⚠️ No se pudo importar audioop_lts. El audio puede no funcionar.")
        audioop = None

if audioop:
    sys.modules["audioop"] = audioop
# ----------------------------------------------------


import discord
from discord.ext import tasks, commands
from gtts import gTTS

# =========================
# 🧰 CONFIGURACIÓN
# =========================
TOKEN = os.getenv("TOKEN")  # Variable de entorno en Render
VOICE_CHANNEL_ID = 1256002493951770697  # Canal de voz

TEXT_CHANNEL_PHRASES: dict[int, str] = {
    1284336904095010826: "premio en espera",
}

MONTO_CHANNELS: dict[int, str] = {
    1414043464194064514: "chat interno",
}

CHANNEL_COOLDOWN_SECONDS: dict[int, int] = {
    1256282483880890504: 3,
    1284336904095010826: 3,
    1414043464194064514: 3,
}
DEFAULT_CHANNEL_COOLDOWN = 180
BLOCKING_ROLE_NAMES = {"supervisor"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
Path(AUDIO_DIR).mkdir(exist_ok=True)

PHRASE_FILES: dict[int, str] = {
    cid: os.path.join(AUDIO_DIR, f"tts_fixed_{cid}.mp3")
    for cid in TEXT_CHANNEL_PHRASES.keys()
}
TMP_TTS = os.path.join(AUDIO_DIR, "_tts_last.mp3")

FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "bin", "ffmpeg.exe")
IDLE_DISCONNECT_SECONDS = 0

avisos = {
    time(11, 59): "bono_crownManual.mp3",
    time(12, 59): "bonoApagar.mp3",
    time(17, 59): "bono_crown.mp3",
}

# =========================
# 🤖 BOT
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ultimo_minuto = None
voice_client: Optional[discord.VoiceClient] = None
voice_last_use: float = 0.0
channel_cooldowns: dict[int, float] = {}

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# =========================
# 🔧 UTILIDADES
# =========================
def full_audio_path(filename: str) -> str:
    return os.path.join(AUDIO_DIR, filename)

def make_ffmpeg_pcm_source(path: str) -> discord.FFmpegPCMAudio:
    before = "-nostdin -re"
    opts = "-vn"
    exe = FFMPEG_PATH or "ffmpeg"
    return discord.FFmpegPCMAudio(source=path, executable=exe, before_options=before, options=opts)

async def ensure_voice_connected(channel: discord.VoiceChannel):
    global voice_client
    if voice_client and voice_client.is_connected() and voice_client.channel.id == channel.id:
        return voice_client
    if voice_client:
        try:
            await voice_client.disconnect(force=True)
        except:
            pass
    voice_client = await channel.connect(reconnect=True, timeout=15.0, self_deaf=True)
    return voice_client

async def play_path(full_path: str):
    global voice_last_use
    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not isinstance(channel, discord.VoiceChannel):
        print("⚠️ Canal de voz no encontrado.")
        return
    if not os.path.isfile(full_path):
        print(f"❌ Archivo no encontrado: {full_path}")
        return

    vc = await ensure_voice_connected(channel)
    if not vc:
        print("💥 No hay conexión de voz.")
        return

    if vc.is_playing():
        vc.stop()
        await asyncio.sleep(0.1)

    done = asyncio.Event()

    def after_playback(error):
        if error:
            print(f"💥 Error en reproducción: {error}")
        bot.loop.call_soon_threadsafe(done.set)

    vc.play(make_ffmpeg_pcm_source(full_path), after=after_playback)
    print(f"▶️ Reproduciendo {full_path}")
    await done.wait()
    voice_last_use = asyncio.get_event_loop().time()

def tts_to_file(text: str, out_path: str, lang: str = "es", tld: str = "com.ar"):
    text = text.strip()[:400]
    gTTS(text=text, lang=lang, tld=tld).save(out_path)

# =========================
# 📅 EVENTOS / TAREAS
# =========================
@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user}")
    await asyncio.sleep(3)  # Espera para evitar el error 4006
    ch = bot.get_channel(VOICE_CHANNEL_ID)
    if isinstance(ch, discord.VoiceChannel):
        try:
            await ensure_voice_connected(ch)
            print(f"🎧 Conectado al canal de voz: {ch.name}")
        except Exception as e:
            print(f"💥 Error al conectar al canal de voz: {e}")
    check_time.start()

@tasks.loop(seconds=10)
async def check_time():
    global ultimo_minuto
    ahora = datetime.now()
    minuto_actual = (ahora.hour, ahora.minute)
    if minuto_actual == ultimo_minuto:
        return
    for horario, audio in avisos.items():
        if ahora.hour == horario.hour and ahora.minute == horario.minute:
            print(f"🔊 Programado {audio}")
            await play_path(full_audio_path(audio))
            ultimo_minuto = minuto_actual
            break

# =========================
# 🚀 COMANDOS
# =========================
@bot.command()
async def decir(ctx, *, texto: str):
    tts_to_file(texto, TMP_TTS)
    await play_path(TMP_TTS)
    await ctx.reply("🗣️ Leído.")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Falta el TOKEN (Render env var).")
        sys.exit(1)
    bot.run(TOKEN)
