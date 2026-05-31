import os
import re
import time
import sys
import json
import yt_dlp
from pathlib import Path
from playwright.sync_api import sync_playwright

# Gelişmiş arayüz için Rich kütüphanesi
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.text import Text
from rich.table import Table
from rich import print as rprint

# --- AYAR SİSTEMİ EKLENTİSİ ---
APP_NAME = "GokturkMediaDownloader"
CONFIG_DIR = Path(os.getenv('APPDATA')) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

def ayar_yukle():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        default_path = str(Path.home() / "Desktop" / "Indirilen_Mediyalar")
        ayarlar = {"indirme_dizini": default_path}
        with open(CONFIG_FILE, "w") as f: json.dump(ayarlar, f)
        return ayarlar
    with open(CONFIG_FILE, "r") as f: return json.load(f)

def ayar_kaydet(yeni_yol):
    ayarlar = {"indirme_dizini": yeni_yol}
    with open(CONFIG_FILE, "w") as f: json.dump(ayarlar, f)
    rprint("[bold green]✓ Ayarlar başarıyla kaydedildi![/bold green]")

console = Console()

# KLASÖRÜ BAŞLANGIÇTA OTOMATİK OLUŞTURMA VE AYAR YÜKLEME
ayarlar = ayar_yukle()
INDIRME_KLASORU = ayarlar["indirme_dizini"]
if not os.path.exists(INDIRME_KLASORU):
    os.makedirs(INDIRME_KLASORU)

OPERASYON_RAPORU = []

def klasor_hazirla(ana_klasor, alt_klasor=""):
    """Dizi adı ve sezona göre klasör mimarisi oluşturur."""
    temiz_ana = re.sub(r'[\\/*?:"<>|]', "", ana_klasor).strip()
    yol = os.path.join(INDIRME_KLASORU, temiz_ana)
    if alt_klasor:
        temiz_alt = re.sub(r'[\\/*?:"<>|]', "", alt_klasor).strip()
        yol = os.path.join(yol, temiz_alt)
    if not os.path.exists(yol):
        os.makedirs(yol)
    return yol

def animasyonlu_baslik(metin):
    panel = Panel(
        Text(metin, justify="center", style="bold gold1"),
        border_style="cyan",
        title="[ GOKTURK MEDYA INDIRME MERKEZI V4.5 ]",
        subtitle="Siber Indirme Istasyonu"
    )
    console.print(panel)

def ytdlp_ilerleme_cubugu(d):
    if d['status'] == 'downloading':
        toplam = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        indirilen = d.get('downloaded_bytes', 0)
        if 'rich_progress' in d['info_dict']:
            progress = d['info_dict']['rich_progress']
            task = d['info_dict']['rich_task_id']
            progress.update(task, completed=indirilen, total=toplam)

def videoyu_indir_gelismis(url, klasor_yolu, dosya_adi, sadece_ses=False, playlist_mi=False):
    """Her mod için optimize edilmiş kararlı indirme motoru."""
    cikis_sablonu = os.path.join(klasor_yolu, f"{dosya_adi}.%(ext)s")
    tipe_gore = "MP3" if sadece_ses else "MP4"
    
    ydl_opts = {
        'outtmpl': cikis_sablonu,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [ytdlp_ilerleme_cubugu],
        'retries': 5,
        'fragment_retries': 5,
        'ignoreerrors': True,
    }
    
    # Playlist mi yoksa tekil video mu olduğunu yt-dlp'ye kesin olarak bildiriyoruz
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
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold cyan"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        
        task_id = progress.add_task(f"[..] Baglanti Kuruluyor...", total=100)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                # Eğer Playlist modu aktifse ve içeride birden fazla video varsa
                if playlist_mi and info and 'entries' in info:
                    entries = list(info['entries'])
                    progress.update(task_id, description=f"[+] {len(entries)} Sarki Siralandi")
                    
                    for idx, entry in enumerate(entries):
                        if not entry: continue
                        v_title = entry.get('title', f"Sarki_{idx+1}")
                        progress.update(task_id, description=f"[>] {v_title[:15]}...")
                        entry['rich_progress'] = progress
                        entry['rich_task_id'] = task_id
                        try:
                            ydl.process_info(entry)
                            OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "BASARILI", "green"))
                        except:
                            OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "HATA", "red"))
                else:
                    # Tekli İndirme Modu
                    v_title = info.get('title', dosya_adi) if info else dosya_adi
                    progress.update(task_id, description=f"[>] {v_title[:15]}...")
                    info['rich_progress'] = progress
                    info['rich_task_id'] = task_id
                    ydl.process_info(info)
                    OPERASYON_RAPORU.append((v_title[:25], tipe_gore, "BASARILI", "green"))
                
                progress.update(task_id, description="[+] Bitti!")
            except Exception as e:
                progress.update(task_id, description="[-] Basarisiz!")
                OPERASYON_RAPORU.append((dosya_adi[:25], tipe_gore, "HATA", "red"))

def m3u8_linki_yakala(url):
    yakalanan_link = None
    with console.status("[bold yellow]Gokturk Botu calisiyor, gizli kaynaklar araniyor...[/bold yellow]", spinner="bouncingBar"):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            
            def istek_kontrol(request):
                nonlocal yakalanan_link
                if ".m3u8" in request.url and "playlist" not in request.url:
                    if not yakalanan_link: yakalanan_link = request.url

            page.on("request", istek_kontrol)
            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
                time.sleep(2)
                tıklanacaklar = ["div.play-button", "iframe", "video", ".player", "#player", ".play-btn"]
                for secici in tıklanacaklar:
                    if yakalanan_link: break
                    try:
                        el = page.locator(secici).first
                        if el.is_visible(): el.click(force=True); time.sleep(1)
                    except: continue
            except: pass
            finally: browser.close()
    return yakalanan_link

def link_sablonu_olustur(ornek_link):
    sayilar = re.findall(r'\d+', ornek_link)
    if len(sayilar) < 2: return None, None, None, "Dizi"
    
    dizi_adi = "Bilinmeyen Dizi"
    parcalar = ornek_link.split('/')
    for p in parcalar:
        if "dizi" in p or "izle" in p or len(p) < 3: continue
        if "-" in p or "_" in p:
            dizi_adi = p.replace("-", " ").replace("_", " ").title()
            break
            
    ornek_sezon, ornek_bolum = int(sayilar[-2]), int(sayilar[-1])
    sablon_link = ornek_link
    r_matches = list(re.finditer(r'\d+', ornek_link))
    b_start, b_end = r_matches[-1].span()
    sablon_link = sablon_link[:b_start] + "{bolum}" + sablon_link[b_end:]
    r_matches2 = list(re.finditer(r'\d+', sablon_link))
    s_start, s_end = r_matches2[-1].span()
    sablon_link = sablon_link[:s_start] + "{sezon}" + sablon_link[s_end:]
    return sablon_link, ornek_sezon, ornek_bolum, dizi_adi

def final_raporu_yazdir():
    if not OPERASYON_RAPORU: return
    table = Table(title="RAPOR: GOKTURK MEDYA OPERASYONU", title_style="bold magenta")
    table.add_column("Medya Adi", style="cyan")
    table.add_column("Tur", style="yellow")
    table.add_column("Durum", style="bold")
    for idx, (isim, tur, durum, renk) in enumerate(OPERASYON_RAPORU):
        if idx > 25: 
            table.add_row("... ve digerleri ...", "-", "-", "white")
            break
        table.add_row(isim, tur, f"[{renk}]{durum}[/{renk}]")
    console.print("\n")
    console.print(table)

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    animasyonlu_baslik(" GOKTURK MEDYA ISTASYONUNA HOS GELDINIZ ")
    
    rprint("\n[bold magenta]-> Lutfen Yapmak Istediginiz Modu Secin:[/bold magenta]")
    rprint("[bold green][1][/bold green] Dizi Modu (Ornek Linkten Akilli Sezon/Bolum Araligi Indir)")
    rprint("[bold green][2][/bold green] Dogrudan Video/Film Indir (Tek Link veya Liste)")
    rprint("[bold green][3][/bold green] Muzik Indirme Modu (MP3 - YouTube & Spotify)")
    rprint("[bold cyan][4][/bold cyan] Ayarlar (Dizin Degistir)")
    
    secim = console.input("\n[bold cyan]Seciminiz (1/2/3/4): [/bold cyan]").strip()
    
    if secim == "4":
        yeni = console.input("\n[bold yellow]Yeni tam dizin yolunu girin: [/bold yellow]").strip()
        if os.path.exists(os.path.dirname(yeni)):
            ayar_kaydet(yeni)
        else:
            rprint("[bold red]Hata: Klasör yolu geçersiz![/bold red]")
        sys.exit()

    elif secim == "1":
        ornek_link = console.input("\n[bold yellow]✍ Ornek bir bolum linki yapistirin: [/bold yellow]").strip()
        sablon, o_sezon, o_bolum, dizi_adi = link_sablonu_olustur(ornek_link)
        if not sablon:
            rprint("[bold red]❌ Link yapisi cozulemedi![/bold red]"); exit()
            
        rprint(f"[bold green]✓ Algilanan Dizi:[/bold green] {dizi_adi} | [bold green]Sezon:[/bold green] {o_sezon} | [bold green]Bolum:[/bold green] {o_bolum}")
        s_bas = int(console.input("[bold cyan]> Baslangic Sezonu: [/bold cyan]"))
        b_bas = int(console.input("[bold cyan]> Baslangic Bolumu: [/bold cyan]"))
        s_bit = int(console.input("[bold red]■ Bitis Sezonu: [/bold red]"))
        b_bit = int(console.input("[bold red]■ Bitis Bölümü: [/bold red]"))
        
        current_s, current_b = s_bas, b_bas
        while True:
            url = sablon.format(sezon=current_s, bolum=current_b)
            dosya_adi = f"Sezon_{current_s}_Bolum_{current_b}"
            kayit_klasoru = klasor_hazirla(dizi_adi, f"Sezon {current_s}")
            m3u8_url = m3u8_linki_yakala(url)
            if m3u8_url:
                videoyu_indir_gelismis(m3u8_url, kayit_klasoru, dosya_adi, sadece_ses=False)
            else:
                rprint(f"[bold red]❌ Kaynak bulunamadi: Sezon {current_s} Bolum {current_b}[/bold red]")
                OPERASYON_RAPORU.append((dosya_adi, "MP4", "BULUNAMADI", "red"))
            if current_s == s_bit and current_b == b_bit: break
            current_b += 1
            if current_b > 30 and current_s < s_bit: current_s += 1; current_b = 1

    elif secim == "2":
        rprint("\n[bold yellow]✍ Indirmek istediginiz video linklerini girin.[/bold yellow]")
        rprint("[bold dim]Baslatmak icin bos birakip Enter'a basin.[/bold dim]")
        linkler = []
        while True:
            l = console.input(f"[bold cyan]-> {len(linkler)+1}. Link: [/bold cyan]").strip()
            if not l: break
            linkler.append(l)
            
        for i, link in enumerate(linkler):
            if "youtube.com" in link or "youtu.be" in link or "instagram.com" in link or "tiktok.com" in link:
                kayit_klasoru = klasor_hazirla("Sosyal Medya Videolari")
                videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=False, playlist_mi=False)
            else:
                kayit_klasoru = klasor_hazirla("Filmler ve Tekli Videolar")
                m3u8_url = m3u8_linki_yakala(link)
                if m3u8_url:
                    dosya = link.split("/")[-2] if link.endswith('/') else link.split("/")[-1]
                    videoyu_indir_gelismis(m3u8_url, kayit_klasoru, dosya[:20], sadece_ses=False)
                else:
                    rprint("[bold red]❌ Siteden video kaynagi sokulemedi.[/bold red]")

    elif secim == "3":
        rprint("\n[bold magenta]--- 🎵 MP3 MUZIK INDIRME KANALI ---[/bold magenta]")
        rprint("[bold green][1][/bold green] Tekli YouTube Videosu (Sadece o videoyu MP3 yapar)")
        rprint("[bold green][2][/bold green] YouTube Playlist / Mix Linki (Tüm listeyi sırayla MP3 yapar)")
        rprint("[bold green][3][/bold green] Spotify Sarki / Playlist Linki (Otomatik MP3 indirir)")
        
        m_secim = console.input("\n[bold cyan]Müzik Modu Seçiniz (1/2/3): [/bold cyan]").strip()
        kayit_klasoru = klasor_hazirla("Indirilen_Muzikler")
        
        if m_secim == "1":
            link = console.input("[bold yellow]✍ Tekli YouTube Video Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)
        elif m_secim == "2":
            link = console.input("[bold yellow]✍ YouTube Playlist / Mix Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(link, kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=True)
        elif m_secim == "3":
            link = console.input("[bold yellow]✍ Spotify Linki: [/bold yellow]").strip()
            videoyu_indir_gelismis(f"ytsearch:{link}", kayit_klasoru, "%(title)s", sadece_ses=True, playlist_mi=False)

    final_raporu_yazdir()
    rprint("\n[bold green]=========================================[/bold green]")
    rprint("[bold gold1]       GOKTURK OPERASYONU BASARIYLA BITTI       [/bold gold1]")
    rprint("[bold green]=========================================[/bold green]")
    console.input("\n[bold white]Kapatmak icin Enter'a basin...[/bold white]")