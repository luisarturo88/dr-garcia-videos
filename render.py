#!/usr/bin/env python3
"""
Renderizador gratuito de videos del Dr. Luis Arturo García.
Entrada: job.json  ->  Salida: out.mp4
  {
    "id": "V012",
    "orientation": "vertical" | "horizontal",
    "voice": "es-EC-LuisNeural",
    "blog_url": "veterinarioluis.com",
    "scenes": [{"text": "...", "image_url": "https://..."}, ...]
  }
Usa: edge-tts (voz neuronal gratis), ffmpeg, Pillow.
"""
import asyncio, json, os, subprocess, sys, textwrap, urllib.request, shutil, math

FAKE_TTS = os.environ.get("FAKE_TTS") == "1"
W_V, H_V = 1080, 1920
W_H, H_H = 1920, 1080
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def sh(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"Fallo: {' '.join(cmd[:6])}...")
    return r.stdout


def dur(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path]).strip())


async def tts_edge(text, voice, mp3):
    import edge_tts
    words = []
    comm = edge_tts.Communicate(text, voice, rate="+6%", boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append((chunk["offset"] / 1e7, (chunk["offset"] + chunk["duration"]) / 1e7, chunk["text"]))
    return words


def tts(text, voice, mp3):
    if FAKE_TTS:  # solo para pruebas sin internet
        n = len(text.split())
        d = n / 2.6
        sh(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{d:.2f}", "-q:a", "9", mp3])
        step = d / max(n, 1)
        return [(i * step, (i + 1) * step, w) for i, w in enumerate(text.split())]
    for intento in range(3):
        try:
            words = asyncio.run(tts_edge(text, voice, mp3))
            if os.path.getsize(mp3) > 1000:
                return words
        except Exception as e:
            sys.stderr.write(f"edge-tts intento {intento+1} falló: {e}\n")
    # Respaldo: gTTS (voz de Google, gratis)
    from gtts import gTTS
    gTTS(text, lang="es", tld="com.mx").save(mp3)
    d = dur(mp3)
    ws = text.split()
    step = d / max(len(ws), 1)
    return [(i * step, (i + 1) * step, w) for i, w in enumerate(ws)]


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(all_words, W, H, path):
    vertical = H > W
    size = 74 if vertical else 62
    marginv = int(H * (0.30 if vertical else 0.27))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,{size},&H00FFFFFF,&H0000D7FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,{marginv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    per = 4 if vertical else 7
    for i in range(0, len(all_words), per):
        grp = all_words[i:i + per]
        start, end = grp[0][0], grp[-1][1]
        # palabra activa en amarillo (karaoke por palabra)
        for j, (ws, we, w) in enumerate(grp):
            txt = " ".join(("{\\c&H00D7FF&}" + x[2] + "{\\c&HFFFFFF&}") if k == j else x[2] for k, x in enumerate(grp))
            ee = grp[j + 1][0] if j + 1 < len(grp) else end
            lines.append(f"Dialogue: 0,{ass_time(ws)},{ass_time(max(ee, ws + 0.05))},Sub,,0,0,0,,{txt}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")


def make_overlay(W, H, blog, path):
    """Capa fija: franja con nombre del doctor + foto del doctor + blog."""
    from PIL import Image, ImageDraw, ImageFont
    vertical = H > W
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f1 = ImageFont.truetype(FONT_BOLD, 40 if vertical else 40)
    f2 = ImageFont.truetype(FONT_BOLD, 40 if vertical else 36)
    # franja superior
    bar_h = 110 if vertical else 90
    d.rectangle([0, 0, W, bar_h], fill=(0, 105, 92, 215))
    t1 = "Dr. Luis Arturo García · Médico Veterinario"
    tw = d.textlength(t1, font=f1)
    d.text(((W - tw) / 2, (bar_h - 50) / 2), t1, font=f1, fill=(255, 255, 255, 255))
    # foto del doctor en círculo (abajo a la izquierda) + cinta del blog
    from PIL import ImageOps
    foto = Image.open(os.path.join(ASSETS, "luis.png")).convert("RGBA")
    cara = foto.crop((5, 0, 175, 170))
    D = 230 if vertical else 190
    cara = ImageOps.fit(cara, (D, D), Image.LANCZOS)
    mask = Image.new("L", (D, D), 0); ImageDraw.Draw(mask).ellipse([0, 0, D, D], fill=255)
    fondo = Image.new("RGBA", (D, D), (255, 255, 255, 255)); fondo.alpha_composite(cara)
    av = Image.new("RGBA", (D + 16, D + 16), (0, 0, 0, 0))
    ImageDraw.Draw(av).ellipse([0, 0, D + 15, D + 15], fill=(255, 193, 7, 255))
    av.paste(fondo, (8, 8), mask)
    blog_h = 84 if vertical else 70
    y_av = H - av.height - (40 if vertical else 24)
    ov.alpha_composite(av, (24, y_av))
    t2 = f"Guía completa en {blog}"
    bw = d.textlength(t2, font=f2) + 60
    x0 = 24 + av.width + 12
    if x0 + bw > W - 16:
        f2 = ImageFont.truetype(FONT_BOLD, 34 if vertical else 32)
        bw = d.textlength(t2, font=f2) + 50
    y_blog = y_av + (av.height - blog_h) // 2
    d.rounded_rectangle([x0, y_blog, x0 + bw, y_blog + blog_h], radius=24, fill=(255, 193, 7, 240))
    d.text((x0 + 26, y_blog + (blog_h - 44) / 2), t2, font=f2, fill=(20, 20, 20, 255))
    ov.save(path)


def main(job_path, out_path):
    job = json.load(open(job_path, encoding="utf-8"))
    vertical = job.get("orientation", "vertical") == "vertical"
    W, H = (W_V, H_V) if vertical else (W_H, H_H)
    voice = job.get("voice", "es-EC-LuisNeural")
    blog = job.get("blog_url", "veterinarioluis.com")
    tmp = "work"
    shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)

    all_words, clips, audios, t0 = [], [], [], 0.0
    for i, sc in enumerate(job["scenes"]):
        img = f"{tmp}/img{i}.jpg"; mp3 = f"{tmp}/a{i}.mp3"; clip = f"{tmp}/c{i}.mp4"
        req = urllib.request.Request(sc["image_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(img, "wb") as f:
            f.write(r.read())
        words = tts(sc["text"], voice, mp3)
        d = dur(mp3) + 0.25
        all_words += [(a + t0, b + t0, w) for a, b, w in words]
        t0 += d
        frames = int(d * 30)
        # imagen que llena toda la pantalla (cover) + zoom lento (Ken Burns)
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='min(1+0.0009*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30,"
              f"format=yuv420p")
        sh(["ffmpeg", "-y", "-loop", "1", "-i", img, "-i", mp3, "-vf", vf, "-af", "apad",
            "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", clip])
        clips.append(clip)

    with open(f"{tmp}/list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    joined = f"{tmp}/joined.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy", joined])

    build_ass(all_words, W, H, f"{tmp}/subs.ass")
    make_overlay(W, H, blog, f"{tmp}/overlay.png")
    sh(["ffmpeg", "-y", "-i", joined, "-i", f"{tmp}/overlay.png",
        "-filter_complex", f"[0:v][1:v]overlay=0:0,ass={tmp}/subs.ass[v]",
        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out_path])
    print(json.dumps({"ok": True, "duration": round(dur(out_path), 2), "file": out_path}))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "job.json", sys.argv[2] if len(sys.argv) > 2 else "out.mp4")
