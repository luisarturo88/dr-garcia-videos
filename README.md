# Videos Dr. Luis Arturo García
Renderizador automático (GitHub Actions + ffmpeg + edge-tts) usado por n8n. Costo: $0 (repo público).

## Formato del trabajo (`job`)
```json
{
  "id": "V012",
  "orientation": "vertical | horizontal",
  "voice": "es-EC-LuisNeural",
  "blog_url": "veterinarioluis.com",
  "scenes": [
    {"text": "narración", "image_url": "https://..."},
    {"text": "narración", "image_query": "sick dog veterinarian"}
  ],
  "cover": {"text": "PUEDE SER MORTAL"}
}
```
- `image_url`: foto ya elegida. `image_query`: el renderizador la busca en Pexels con el secreto `PEXELS_API_KEY`.
  Si no hay foto, usa un fondo degradado (el video nunca se cae por una imagen).
- `cover.text` (opcional): activa el texto-gancho enorme en los primeros 3 s del short y genera
  `cover_h.jpg` (1280x720, miniatura de YouTube) y `cover_v.jpg` (1080x1920, TikTok/Reels).
  Sin `cover`, el comportamiento es idéntico al anterior.

## Secretos del repo
- `PEXELS_API_KEY`: clave de pexels.com/api (Settings > Secrets and variables > Actions).

## Salida
Release con etiqueta `job_id` que contiene `video.mp4` (y `cover_h.jpg`, `cover_v.jpg` si hubo `cover`).
