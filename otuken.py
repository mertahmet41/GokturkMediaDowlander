import os
import re
import sys
import time
import json
import shutil
import urllib.request
import urllib.parse
from pathlib import Path

import yt_dlp
from playwright.sync_api import sync_playwright

# Windows Türkçe (CP1254) terminalinde Unicode (✓, ⚡ vb.) çökmesini önle
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    os.system("")  # Windows ANSI/VT100 desteğini aktif eder

# Gelişmiş arayüz için Rich kütüphanesi
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.text import Text
from rich.table import Table
from rich import print as rprint

# --- AYAR SİSTEMİ ---
APP_NAME = "GokturkMediaDownloader"
# Windows ve Linux/macOS uyumlu ayar dizini
_appdata = os.getenv('APPDATA')
CONFIG_DIR = Path(_appdata) / APP_NAME if _appdata else Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"


def ayar_yukle():
    """Kullanıcı ayarlarını yükler veya varsayılan oluşturur."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        default_path = str(Path.home() / "Desktop" / "Indirilen_Mediyalar")
        ayarlar = {"indirme_dizini": default_path}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=2)
        return ayarlar
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def ayar_kaydet(yeni_yol):
    """Yeni indirme dizinini kaydeder."""
    ayarlar = {"indirme_dizini": yeni_yol}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(ayarlar, f, ensure_ascii=False, indent=2)
    rprint("[bold green]✓ Ayarlar başarıyla kaydedildi![/bold green]")


console = Console()

ayarlar = ayar_yukle()
INDIRME_KLASORU = ayarlar["indirme_dizini"]
if not os.path.exists(INDIRME_KLASORU):
    os.makedirs(INDIRME_KLASORU, exist_ok=True)

OPERASYON_RAPORU = []


def dosya_adi_temizle(isim, varsayilan="medya"):
    """Windows/Linux işletim sistemlerinde dosya adında geçersiz karakterleri temizler."""
    if not isim or not isinstance(isim, str):
        return varsayilan
    # Eğer yt-dlp şablonu ise dokunma
    if "%(" in isim and ")s" in isim:
        return isim
    # Eğer doğrudan URL verildiyse dosya adı kısmını al
    if isim.startswith("http://") or isim.startswith("https://"):
        parsed = urllib.parse.urlparse(isim)
        path = parsed.path.rstrip("/")
        isim = path.split("/")[-1] if "/" in path else varsayilan
    # Geçersiz karakterleri kaldır (\ / : * ? " < > |)
    temiz = re.sub(r'[\\/*?:"<>|]', "", isim).strip()
    return temiz if temiz else varsayilan


def klasor_hazirla(ana_klasor, alt_klasor=""):
    """Dizi adı ve sezona göre klasör mimarisi oluşturur."""
    temiz_ana = dosya_adi_temizle(ana_klasor, varsayilan="Dizi")
    yol = os.path.join(INDIRME_KLASORU, temiz_ana)
    if alt_klasor:
        temiz_alt = dosya_adi_temizle(alt_klasor, varsayilan="Sezon")
        yol = os.path.join(yol, temiz_alt)
    os.makedirs(yol, exist_ok=True)
    return yol


def animasyonlu_baslik(metin):
    """Açılış banner paneli."""
    panel = Panel(
        Text(metin, justify="center", style="bold gold1"),
        border_style="cyan",
        title="[ GOKTURK MEDYA INDIRME MERKEZI V5.0 ]",
        subtitle="Siber Otomatik Otomasyon Istasyonu"
    )
    console.print(panel)


def make_progress_hook(progress, task_id):
    """yt-dlp çıktısını KeyError vermeden Rich çubuğuna aktaran güvenli kanca."""
    def hook(d):
        status = d.get('status')
        if status == 'downloading':
            toplam = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            indirilen = d.get('downloaded_bytes', 0)
            frag_idx = d.get('fragment_index')
            frag_cnt = d.get('fragment_count')

            if frag_idx and frag_cnt:
                desc = f"[bold cyan][>] Parça indiriliyor: {frag_idx}/{frag_cnt}[/bold cyan]"
            else:
                desc = "[bold blue][>] Medya indiriliyor...[/bold blue]"

            progress.update(task_id, completed=indirilen, total=toplam or None, description=desc)

        elif status == 'finished':
            progress.update(task_id, description="[bold gold1][⚡] Parçalar birleştiriliyor (MP4/MP3)...[/bold gold1]")

    return hook


def spotify_bilgisi_al(url):
    """Spotify linklerinden oEmbed API ile şarkı/sanatçı başlığını çözer."""
    try:
        api_url = f"https://open.spotify.com/oembed?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(
            api_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            title = data.get('title')
            if title:
                return f"{title} audio"
    except Exception:
        pass
    return url


def videoyu_indir_gelismis(url, klasor_yolu, dosya_adi, sadece_ses=False, playlist_mi=False):
    """Zaman aşımı korumalı, hata kontrollü gelişmiş indirme motoru."""
    temiz_dosya = dosya_adi_temizle(dosya_adi)
    cikis_sablonu = os.path.join(klasor_yolu, f"{temiz_dosya}.%(ext)s")
    tipe_gore = "MP3" if sadece_ses else "MP4"

    js_runtimes = {}
    if shutil.which("node"):
        js_runtimes["node"] = {}
    if shutil.which("deno"):
        js_runtimes["deno"] = {}

    ydl_opts = {
        'outtmpl': cikis_sablonu,
        'quiet': True,
        'noprogress': True,
        'no_warnings': True,
        'retries': 3,
        'fragment_retries': 5,
        'ignoreerrors': True,
        'timeout': 30,
        'extractor_args': {
            'youtube': {
                'player_client': ['web_creator', 'ios', 'android', 'web', 'mweb']
            }
        }
    }
    if js_runtimes:
        ydl_opts['js_runtimes'] = js_runtimes

    if playlist_mi:
        ydl_opts.update({'noplaylist': False, 'extract_flat': False})
    else:
        ydl_opts.update({'noplaylist': True, 'extract_flat': False})

    if sadece_ses:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'remux_video': 'mp4',
        })

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold cyan"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task_id = progress.add_task("[bold yellow][..] Bağlantı kuruluyor...[/bold yellow]", total=100)
        ydl_opts['progress_hooks'] = [make_progress_hook(progress, task_id)]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    progress.update(task_id, description="[bold red][-] Kaynak bulunamadı![/bold red]")
                    OPERASYON_RAPORU.append((temiz_dosya[:25], tipe_gore, "BULUNAMADI", "red"))
                    return False

                if playlist_mi and 'entries' in info:
                    entries = [e for e in info['entries'] if e]
                    for entry in entries:
                        v_title = entry.get('title', temiz_dosya)
                        OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "BASARILI", "green"))
                else:
                    v_title = info.get('title', temiz_dosya)
                    OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "BASARILI", "green"))

                progress.update(task_id, description="[bold green][✓] Tamamlandı![/bold green]")
                return True
        except Exception as e:
            progress.update(task_id, description="[bold red][-] İndirme Başarısız Oldu![/bold red]")
            OPERASYON_RAPORU.append((temiz_dosya[:25], tipe_gore, "HATA", "red"))
            return False


def m3u8_linki_yakala(url):
    """Playwright ile arka planda sayfayı yükleyip .m3u8 medya akış linkini yakalar."""
    yakalanan_link = None
    with console.status("[bold yellow]Gokturk Botu çalışıyor, medya kaynakları taranıyor...[/bold yellow]", spinner="bouncingBar"):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
                page = context.new_page()

                def istek_kontrol(request):
                    nonlocal yakalanan_link
                    req_url = request.url
                    # Bilinen reklam sağlayıcılarını filtrele
                    if any(ad in req_url.lower() for ad in ["googleads", "doubleclick", "adservice", "popads", "trafficjunky"]):
                        return
                    if ".m3u8" in req_url.lower():
                        if not yakalanan_link:
                            yakalanan_link = req_url

                def yanit_kontrol(response):
                    nonlocal yakalanan_link
                    if yakalanan_link:
                        return
                    ct = response.headers.get("content-type", "").lower()
                    if "mpegurl" in ct or "application/x-mpegurl" in ct:
                        yakalanan_link = response.url

                page.on("request", istek_kontrol)
                page.on("response", yanit_kontrol)

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    time.sleep(3)

                    # Video oynatma tetikleyicileri
                    tiklanacaklar = [
                        "div.play-button", ".play-btn", "[class*='play']",
                        ".vjs-big-play-button", "button.jw-display-icon-container",
                        "video", "iframe", "#player", ".player"
                    ]

                    for secici in tiklanacaklar:
                        if yakalanan_link:
                            break
                        try:
                            el = page.locator(secici).first
                            if el.is_visible():
                                el.click(force=True)
                                time.sleep(1.5)
                        except Exception:
                            continue

                    if not yakalanan_link:
                        page.mouse.click(640, 360)
                        time.sleep(2)
                        if not yakalanan_link:
                            page.mouse.click(640, 360)
                            time.sleep(2)

                except Exception:
                    pass
                finally:
                    browser.close()
        except Exception as e:
            rprint(f"[bold red]Tarayıcı motoru hatası: {e}[/bold red]")

    return yakalanan_link


def _make_placeholder(name, orig_str):
    if len(orig_str) > 1 and orig_str.startswith('0'):
        return '{' + f'{name}:0{len(orig_str)}d' + '}'
    return '{' + name + '}'


def link_sablonu_olustur(ornek_link):
    """Örnek bölüm linkinden dizi adı, sezon ve bölüm şablonunu ayrıştırır."""
    if not ornek_link or not ornek_link.strip():
        return None, None, None, "Dizi"

    url = ornek_link.strip()
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path
    if not path or path == '/':
        path = parsed.query

    path_decoded = urllib.parse.unquote(path)

    s_val, b_val = None, None
    s_span, b_span = None, None
    s_orig, b_orig = "", ""

    # 1. Compact: S01E02 or s1e2
    m_se = re.search(r'[sS](\d+)[eE](\d+)', path_decoded)
    if m_se:
        s_orig, b_orig = m_se.group(1), m_se.group(2)
        s_val, b_val = int(s_orig), int(b_orig)
        s_span, b_span = m_se.span(1), m_se.span(2)

    # 2. 1x02 or 01x02
    if s_val is None:
        m_x = re.search(r'(?:^|[\/\-_])(\d+)[xX](\d+)(?:[\/\-_]|$)', path_decoded)
        if m_x:
            s_orig, b_orig = m_x.group(1), m_x.group(2)
            s_val, b_val = int(s_orig), int(b_orig)
            s_span, b_span = m_x.span(1), m_x.span(2)

    # 3. Explicit keywords: sezon / season and bolum / episode
    if s_val is None or b_val is None:
        m_s_before = re.search(r'(?:^|[\/\-_])(\d+)[-_]?(?:sezon|season)(?:[\/\-_]|$)', path_decoded, re.IGNORECASE)
        m_s_after = re.search(r'(?:sezon|season)[-_]?(\d+)(?:[\/\-_]|$)', path_decoded, re.IGNORECASE)

        m_b_before = re.search(r'(?:^|[\/\-_])(\d+)[-_]?(?:bolum|bölüm|episode|ep)(?:[\/\-_]|$)', path_decoded, re.IGNORECASE)
        m_b_after = re.search(r'(?:bolum|bölüm|episode|ep)[-_]?(\d+)(?:[\/\-_]|$)', path_decoded, re.IGNORECASE)

        if s_val is None:
            if m_s_before:
                s_orig = m_s_before.group(1)
                s_val = int(s_orig)
                s_span = m_s_before.span(1)
            elif m_s_after:
                s_orig = m_s_after.group(1)
                s_val = int(s_orig)
                s_span = m_s_after.span(1)

        if b_val is None:
            if m_b_before:
                b_orig = m_b_before.group(1)
                b_val = int(b_orig)
                b_span = m_b_before.span(1)
            elif m_b_after:
                b_orig = m_b_after.group(1)
                b_val = int(b_orig)
                b_span = m_b_after.span(1)

    # 4. If episode found but season not found: default season=1
    if b_val is not None and s_val is None:
        s_val = 1
        s_span = None

    # 5. Fallback numbers in path (domain digits are strictly excluded)
    if b_val is None:
        num_matches = list(re.finditer(r'\d+', path_decoded))
        if len(num_matches) >= 2:
            s_match, b_match = num_matches[-2], num_matches[-1]
            s_orig, b_orig = s_match.group(0), b_match.group(0)
            s_val, b_val = int(s_orig), int(b_orig)
            s_span, b_span = s_match.span(0), b_match.span(0)
        elif len(num_matches) == 1:
            b_match = num_matches[0]
            b_orig = b_match.group(0)
            s_val, b_val = 1, int(b_orig)
            s_span, b_span = None, b_match.span(0)
        else:
            return None, None, None, "Dizi"

    # Reconstruct template preserving domain and path
    replacements = []
    if b_span:
        replacements.append((b_span[0], b_span[1], _make_placeholder("bolum", b_orig)))
    if s_span and s_span != b_span:
        replacements.append((s_span[0], s_span[1], _make_placeholder("sezon", s_orig)))

    replacements.sort(key=lambda x: x[0], reverse=True)
    new_path = path_decoded
    for start, end, rep in replacements:
        new_path = new_path[:start] + rep + new_path[end:]

    sablon_link = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, new_path, parsed.query, parsed.fragment))

    # Extract clean series name
    segments = [seg for seg in path_decoded.strip('/').split('/') if seg]
    candidate = ''
    for seg in segments:
        seg_clean = re.sub(r'\.(html|php|mp4|m3u8|webm)$', '', seg, flags=re.IGNORECASE)
        if seg_clean.lower() in ('dizi', 'diziler', 'watch', 'series', 'film', 'video', 'izle'):
            continue
        candidate = seg_clean
        break

    if not candidate and segments:
        candidate = segments[-1]

    candidate = re.sub(r'(\d+)?[-_]?(sezon|season)[-_]?(\d+)?', '', candidate, flags=re.IGNORECASE)
    candidate = re.sub(r'(\d+)?[-_]?(bolum|bölüm|episode|ep)[-_]?(\d+)?', '', candidate, flags=re.IGNORECASE)
    candidate = re.sub(r'[sS]\d+[eE]\d+', '', candidate)
    candidate = re.sub(r'\d+[xX]\d+', '', candidate)
    candidate = re.sub(r'[-_]?(izle|full|hd|1080p|720p|tek[-_]?parca|turkce[-_]?dublaj|altyazili)[-_]?', '', candidate, flags=re.IGNORECASE)
    candidate = re.sub(r'\d+', '', candidate)
    candidate = re.sub(r'[-_]+', ' ', candidate).strip().title()
    dizi_adi = candidate if candidate else "Dizi"

    return sablon_link, s_val, b_val, dizi_adi


def guvenli_sayi_al(soru, varsayilan=1):
    """Kullanıcıdan güvenli sayı girişi alır, boş veya hatalı girişte varsayılan değeri döner."""
    deger = console.input(soru).strip()
    try:
        return int(deger)
    except (ValueError, TypeError):
        return varsayilan


def final_raporu_yazdir():
    """Operasyon özet tablosunu ekrana basar."""
    if not OPERASYON_RAPORU:
        return
    table = Table(title="RAPOR: GOKTURK MEDYA OPERASYONU", title_style="bold magenta")
    table.add_column("Medya Adı", style="cyan")
    table.add_column("Tür", style="yellow")
    table.add_column("Durum", style="bold")
    for idx, (isim, tur, durum, renk) in enumerate(OPERASYON_RAPORU):
        if idx > 25:
            table.add_row("... ve diğerleri ...", "-", "-", "white")
            break
        table.add_row(isim, tur, f"[{renk}]{durum}[/{renk}]")
    console.print("\n")
    console.print(table)


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    animasyonlu_baslik(" GOKTURK MEDYA ISTASYONUNA HOS GELDINIZ ")

    rprint("\n[bold magenta]-> Lütfen Yapmak İstediğiniz Modu Seçin:[/bold magenta]")
    rprint("[bold green][1][/bold green] Dizi Modu (Örnek Linkten Akıllı Sezon/Bölüm Aralığı İndir)")
    rprint("[bold green][2][/bold green] Doğrudan Video/Film İndir (Tek Link veya Liste)")
    rprint("[bold green][3][/bold green] Müzik İndirme Modu (MP3 - YouTube & Spotify)")
    rprint("[bold cyan][4][/bold cyan] Ayarlar (İndirme Dizinini Değiştir)")

    secim = console.input("\n[bold cyan]Seçiminiz (1/2/3/4): [/bold cyan]").strip()

    if secim == "4":
        yeni = console.input("\n[bold yellow]Yeni tam dizin yolunu girin: [/bold yellow]").strip()
        if yeni and os.path.exists(os.path.dirname(yeni)):
            ayar_kaydet(yeni)
        else:
            rprint("[bold red]Hata: Klasör yolu geçersiz![/bold red]")
        sys.exit()

    elif secim == "1":
        ornek_link = console.input("\n[bold yellow]✍ Örnek bir bölüm linki yapıştırın: [/bold yellow]").strip()
        sablon, o_sezon, o_bolum, dizi_adi = link_sablonu_olustur(ornek_link)
        if not sablon:
            rprint("[bold red]❌ Link yapısı çözülemedi![/bold red]")
            sys.exit()

        rprint(f"[bold green]✓ Algılanan Dizi:[/bold green] {dizi_adi} | [bold green]Sezon:[/bold green] {o_sezon} | [bold green]Bölüm:[/bold green] {o_bolum}")
        s_bas = guvenli_sayi_al(f"[bold cyan]> Başlangıç Sezonu [{o_sezon}]: [/bold cyan]", o_sezon)
        b_bas = guvenli_sayi_al(f"[bold cyan]> Başlangıç Bölümü [{o_bolum}]: [/bold cyan]", o_bolum)
        s_bit = guvenli_sayi_al(f"[bold red]■ Bitiş Sezonu [{s_bas}]: [/bold red]", s_bas)
        b_bit = guvenli_sayi_al(f"[bold red]■ Bitiş Bölümü [{b_bas}]: [/bold red]", b_bas)

        current_s, current_b = s_bas, b_bas
        ardisik_hata = 0

        while True:
            url = sablon.format(sezon=current_s, bolum=current_b)
            dosya_adi = f"Sezon_{current_s}_Bolum_{current_b}"
            kayit_klasoru = klasor_hazirla(dizi_adi, f"Sezon {current_s}")

            max_deneme = 3
            deneme = 0
            basarili = False

            while deneme < max_deneme:
                if deneme > 0:
                    rprint(f"[bold yellow][!] İndirme takıldı veya koptu. Tekrar deneniyor... (Deneme {deneme+1}/{max_deneme})[/bold yellow]")

                m3u8_url = m3u8_linki_yakala(url)
                if m3u8_url:
                    basarili = videoyu_indir_gelismis(m3u8_url, kayit_klasoru, dosya_adi, sadece_ses=False)
                    if basarili:
                        ardisik_hata = 0
                        break
                else:
                    rprint(f"[bold red]❌ Siteden video kaynağı sökülemedi, bekleniyor...[/bold red]")
                    time.sleep(3 * (deneme + 1))
                deneme += 1

            if not basarili:
                ardisik_hata += 1
                rprint(f"[bold red]❌ Kaynak bulunamadı: Sezon {current_s} Bölüm {current_b}[/bold red]")
                OPERASYON_RAPORU.append((dosya_adi, "MP4", "BULUNAMADI", "red"))

            if current_s == s_bit and current_b == b_bit:
                break

            current_b += 1
            # Eğer 3 ardışık bölüm bulunamadıysa muhtemelen sezon bitti
            if ardisik_hata >= 3 and current_s < s_bit:
                rprint(f"[bold yellow]ℹ️ Sezon {current_s} tamamlandı görünüyor. Sezon {current_s + 1}'e geçiliyor...[/bold yellow]")
                current_s += 1
                current_b = 1
                ardisik_hata = 0

    elif secim == "2":
        rprint("\n[bold yellow]✍ İndirmek istediğiniz video linklerini girin.[/bold yellow]")
        rprint("[bold dim]Başlatmak için boş bırakıp Enter'a basın.[/bold dim]")
        linkler = []
        while True:
            l = console.input(f"[bold cyan]-> {len(linkler)+1}. Link: [/bold cyan]").strip()
            if not l:
                break
            linkler.append(l)

        for i, link in enumerate(linkler):
            if any(dom in link for dom in ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", "x.com"]):
                kayit_klasoru = klasor_hazirla("Sosyal Medya Videolari")
                videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=False, playlist_mi=False)
            else:
                kayit_klasoru = klasor_hazirla("Filmler ve Tekli Videolar")
                m3u8_url = m3u8_linki_yakala(link)
                if m3u8_url:
                    ham_isim = link.rstrip("/").split("/")[-1]
                    temiz_isim = dosya_adi_temizle(ham_isim, varsayilan=f"Video_{i+1}")
                    videoyu_indir_gelismis(m3u8_url, kayit_klasoru, temiz_isim[:30], sadece_ses=False)
                else:
                    rprint("[bold red]❌ Siteden video kaynağı sökülemedi.[/bold red]")

    elif secim == "3":
        rprint("\n[bold magenta]--- 🎵 MP3 MÜZİK İNDİRME KANALI ---[/bold magenta]")
        rprint("[bold green][1][/bold green] Tekli YouTube Videosu / Şarkısı (MP3)")
        rprint("[bold green][2][/bold green] YouTube Playlist / Oynatma Listesi (Toplu MP3)")
        rprint("[bold green][3][/bold green] Spotify Şarkı / Parça Linki (Otomatik MP3 İndirir)")

        m_secim = console.input("\n[bold cyan]Müzik Modu Seçiniz (1/2/3): [/bold cyan]").strip()
        kayit_klasoru = klasor_hazirla("Indirilen_Muzikler")

        if m_secim == "1":
            link = console.input("[bold yellow]✍ Tekli YouTube Video Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)
        elif m_secim == "2":
            link = console.input("[bold yellow]✍ YouTube Playlist Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=True)
        elif m_secim == "3":
            link = console.input("[bold yellow]✍ Spotify Şarkı Linki: [/bold yellow]").strip()
            if "spotify.com" in link:
                arama_terimi = spotify_bilgisi_al(link)
                rprint(f"[bold cyan]🔍 Spotify üzerinden aranan parça:[/bold cyan] {arama_terimi}")
                videoyu_indir_gelismis(f"ytsearch1:{arama_terimi}", kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)
            else:
                videoyu_indir_gelismis(f"ytsearch1:{link}", kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)

    final_raporu_yazdir()
    rprint("\n[bold green]=========================================[/bold green]")
    rprint("[bold gold1]       GOKTURK OPERASYONU BASARIYLA BITTI       [/bold gold1]")
    rprint("[bold green]=========================================[/bold green]")
    console.input("\n[bold white]Kapatmak için Enter'a basın...[/bold white]")


if __name__ == "__main__":
    main()
