"""
Göktürk Medya İndirme Merkezi
Siber İndirme İstasyonu - Ana Giriş Noktası
"""
import sys

def main():
    if "--cli" in sys.argv:
        from otuken import main as cli_main
        cli_main()
    else:
        try:
            from gui import main as gui_main
            gui_main()
        except Exception as e:
            print(f"[!] Grafik arayüz başlatılamadı ({e}), komut satırı moduna geçiliyor...")
            from otuken import main as cli_main
            cli_main()

if __name__ == "__main__":
    main()
