# Renderizador de videos - Dr. Luis Arturo García

Fábrica gratuita de videos veterinarios (sin marca de agua, sin límite).

## Formatos soportados
- short: vertical 1080x1920, 30 fps, ~3 minutos (YouTube Shorts / Reels / TikTok)
- medio: horizontal 1920x1080, 24 fps, 12-15 minutos
- masterclass: horizontal 1920x1080, 24 fps, ~30 minutos (codificación rápida)

## Entrada (job.json)
{
  "id": "V012",
  "orientation": "vertical" | "horizontal",
  "formato": "short" | "medio" | "masterclass",
  "voice": "es-EC-LuisNeural",
  "blog_url": "veterinarioluis.com",
  "scenes": [{"text": "...", "image_url": "https://..."}]
}

## Salida
Release con video.mp4 (etiqueta = job_id).

Voz: Microsoft Edge TTS es-EC-LuisNeural (gratis) con respaldo gTTS.
Subtítulos karaoke: la palabra activa se pinta amarilla.
