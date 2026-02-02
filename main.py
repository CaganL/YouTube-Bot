import os
import random
import json
import requests
import sys
import asyncio
import edge_tts
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx, ColorClip

# --- GELİŞMİŞ AYARLAR VE SAĞLAM LİNKLER ---
# Not: Bugün PAZARTESİ olduğu için "KORKU" çalışacak.
SCHEDULE = {
    "Monday":    {"topic": "KORKU", "title": "😱 KORKU SEANSI", "video": "https://cdn.pixabay.com/video/2020/05/25/40139-424930134_tiny.mp4"}, # Sisli Orman
    "Tuesday":   {"topic": "BILGI", "title": "🧠 BEYİN YAKAN BİLGİ", "video": "https://cdn.pixabay.com/video/2019/04/20/22908-331626246_tiny.mp4"}, # Soyut Teknoloji
    "Wednesday": {"topic": "MOTIVASYON", "title": "💪 GÜNÜN MOTİVASYONU", "video": "https://cdn.pixabay.com/video/2020/09/14/49983-460674957_tiny.mp4"}, # Gün batımı
    "Thursday":  {"topic": "BILGI", "title": "🧠 BUNU BİLİYOR MUYDUN?", "video": "https://cdn.pixabay.com/video/2019/04/20/22908-331626246_tiny.mp4"},
    "Friday":    {"topic": "GIZEM", "title": "🕵️‍♂️ GİZEM DOSYALARI", "video": "https://cdn.pixabay.com/video/2020/05/25/40139-424930134_tiny.mp4"},
    "Saturday":  {"topic": "EGZOTIK", "title": "🦜 DOĞANIN MUCİZELERİ", "video": "https://cdn.pixabay.com/video/2020/09/14/49983-460674957_tiny.mp4"},
    "Sunday":    {"topic": "GENEL", "title": "🤔 İLGİNÇ GERÇEKLER", "video": "https://cdn.pixabay.com/video/2019/04/20/22908-331626246_tiny.mp4"}
}

# --- UZUN VE SÜRÜKLEYİCİ İÇERİK HAVUZU ---
CONTENT_POOL = {
    "KORKU": [
        "Rusya'da 'Radyo İstasyonu UVB-76' adında gizemli bir frekans var. 40 yıldır, haftanın 7 günü, günün 24 saati sadece garip bir vızıltı sesi yayınlıyor. Ancak bazen, çok nadiren, vızıltı duruyor ve canlı bir Rus askeri sesi anlamsız kodlar okumaya başlıyor. Bu istasyonun amacı ne? Kıyamet günü silahı mı, yoksa sadece terk edilmiş bir şaka mı? Kimse bilmiyor ama yayın hiç durmuyor.",
        "1990'larda Japonya'da yaşayan bir adam, evindeki yiyeceklerin sürekli kaybolduğundan şüphelenmeye başladı. Başta hafızasını kaybettiğini düşündü. Bir gün mutfağa gizli kamera yerleştirdi. Görüntüleri izlediğinde kanı dondu. Evde kimse yokken, mutfak dolabının en üst rafından yaşlı, tanımadığı bir kadın çıkıyor, yiyecekleri yiyor ve tekrar dolaba girip saklanıyordu. Kadının orada tam bir yıldır yaşadığı ortaya çıktı."
    ],
    "BILGI": [
        "Eğer bir kağıdı 42 kez ikiye katlayabilseydiniz, kalınlığı Dünya'dan Ay'a kadar ulaşırdı. Bu, üstel büyümenin korkutucu gücüdür. Ancak fiziksel olarak bir kağıdı 7 veya 8 kereden fazla katlamak neredeyse imkansızdır, çünkü her katlamada gereken enerji ve kağıdın gerilimi inanılmaz boyutlara ulaşır.",
        "Balinaların okyanusun derinliklerinde söylediği şarkılar o kadar güçlüdür ki, ses dalgaları suyun altında bir jet uçağının kalkışından daha fazla desibele ulaşabilir. Bu sesler, okyanusun diğer ucundaki balinalar tarafından, binlerce kilometre öteden duyulabilir."
    ],
    "MOTIVASYON": [
        "Hayatınızdaki en zor dönemler, aslında sizi gelecekteki en güçlü halinize hazırlayan antrenmanlardır. Şu an içinde bulunduğunuz karanlık, bir tüneldir, bir kuyu değil. Yürümeye devam ederseniz mutlaka ışığı göreceksiniz. Vazgeçtiğiniz an, aslında başarmaya en yakın olduğunuz andır.",
        "Bir bambu ağacı ekildiğinde, ilk 4 yıl boyunca toprağın üzerinde neredeyse hiçbir büyüme göstermez. Tüm enerjisini köklerini derinleştirmeye harcar. Ancak 5. yılda, sadece 6 hafta içinde 27 metre boya ulaşır. Sizin çabalarınız da böyledir. Sonuç göremiyorsanız durmayın, kök salıyorsunuz."
    ],
    "GIZEM": ["Voynich el yazması, 15. yüzyıldan kalma, dünyadaki hiçbir dile benzemeyen bir dille ve tuhaf bitki çizimleriyle dolu bir kitaptır. Yüzlerce kriptolog, hatta yapay zeka bile bu kitabı çözmeyi denedi ama başarısız oldu. Kitabın uzaylılar tarafından mı, yoksa dahi bir şakacı tarafından mı yazıldığı hala büyük bir sır."],
    "EGZOTIK": ["Bir ahtapotun üç kalbi ve dokuz beyni vardır. Ana beyne ek olarak, her kolun kendi küçük beyni bulunur. Bu sayede kollar, ana beyinden bağımsız kararlar alabilir. Hatta bir ahtapotun kolu kopsa bile, o kol bir süre daha hareket etmeye, avlanmaya ve yiyeceği olmayan bir ağıza götürmeye çalışır."],
    "GENEL": ["Tarihteki en kısa savaş, 1896 yılında İngiltere ve Zanzibar arasında yaşanmıştır. Savaş sadece 38 dakika sürmüştür. İngiliz donanmasının gücünü gören Zanzibar sultanı, daha bir saat bile dolmadan teslim bayrağını çekmiştir."]
}

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        print("HATA: TOKEN_JSON bulunamadı!")
        sys.exit(1)
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

async def generate_pro_voice(text, filename="voice.mp3"):
    # Kaliteli ve tok bir ses
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save(filename)

def create_video_pro(text, background_url, title_text):
    print(f"🎬 Sinema Modu Video Hazırlanıyor... Başlık: {title_text}")
    
    # 1. Ses (Uzun)
    asyncio.run(generate_pro_voice(text))
    audio = AudioFileClip("voice.mp3")
    print(f"🎙️ Ses Süresi: {audio.duration} saniye")
    
    # 2. Arka Plan İndirme (Daha Güvenli Linkler)
    print("📥 Yüksek Kaliteli Video indiriliyor...")
    video_downloaded = False
    try:
        # Daha gerçekçi bir tarayıcı taklidi
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(background_url, headers=headers, stream=True, timeout=30)
        if r.status_code == 200:
            with open("background.mp4", 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            # Boyut kontrolü (En az 500KB olmalı)
            if os.path.getsize("background.mp4") > 500000:
                video_downloaded = True
            else:
                 print("⚠️ İndirilen dosya çok küçük (Bozuk olabilir).")
        else:
             print(f"⚠️ İndirme hatası, Sunucu Cevabı: {r.status_code}")
    except Exception as e:
        print(f"⚠️ İndirme hatası: {e}")

    # 3. Video İşleme
    if video_downloaded:
        try:
            background = VideoFileClip("background.mp4")
            # Eğer yataysa dikey yap
            if background.w > background.h:
                 # Ortadan dikey kesit al
                 new_width = background.h * (9/16)
                 background = background.crop(x_center=background.w/2, width=new_width, height=background.h)
            
            # 1080x1920 HD Kaliteye zorla
            background = background.resize(height=1920)
            background = background.crop(x_center=background.w/2, width=1080, height=1920)
            
            # Loop (Sese göre uzat)
            background = background.fx(vfx.loop, duration=audio.duration + 1.5)
            print("✅ Arka plan videosu başarıyla işlendi.")
        except Exception as e:
            print(f"⚠️ Video işleme hatası: {e}. Yedek plana geçiliyor.")
            video_downloaded = False

    # EĞER VİDEO YİNE BOZUKSA -> SİYAH EKRAN (Çökmemesi için son çare)
    if not video_downloaded:
        print("🚨 DİKKAT: Video indirilemedi. Siyah ekran kullanılıyor.")
        background = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=audio.duration + 1.5)

    # 4. Birleştir ve Yazı Ekle
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    # Dinamik Başlık (Konuya göre değişen)
    txt_clip = TextClip(title_text, fontsize=65, color='white', bg_color='#cc0000', # Kırmızı arka planlı yazı
                        size=(900, None), method='caption', align='center')
    # Yazıyı biraz daha yukarı alalım
    txt_clip = txt_clip.set_pos(('center', 150)).set_duration(video.duration)
    
    final_video = CompositeVideoClip([video, txt_clip])
    # Yüksek kalite ayarları (Bitrate artırıldı)
    final_video.write_videofile("shorts_video.mp4", fps=30, bitrate="8000k", codec="libx264", audio_codec="aac", preset='medium')
    return "shorts_video.mp4"

def upload_to_youtube(file_path, title, description, topic):
    try:
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Kategoriye göre etiketler
        tags = ["shorts", "kesfet", topic.lower()]
        if topic == "KORKU": tags.extend(["korku", "paranormal", "gizem"])
        if topic == "BILGI": tags.extend(["ilgincbilgiler", "bilim", "egitim"])

        print(f"YouTube'a yükleniyor... Başlık: {title}")
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "27" # Eğitim/Bilgi
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(file_path)
        )
        response = request.execute()
        print(f"✅ YÜKLEME BAŞARILI! Video ID: {response['id']}")
    except Exception as e:
        print(f"YouTube Yükleme Hatası: {e}")
        sys.exit(1)

def main():
    # Bugünün ayarlarını getir (Pazartesi -> Korku)
    day_name = datetime.now().strftime("%A")
    schedule = SCHEDULE.get(day_name, SCHEDULE["Sunday"])
    
    topic = schedule["topic"]
    title_prefix = schedule["title"]
    bg_video = schedule["video"]
    
    # Uzun hikayeyi seç
    text = random.choice(CONTENT_POOL.get(topic, CONTENT_POOL["GENEL"]))
    
    # Videoyu oluştur
    video_file = create_video_pro(text, bg_video, title_prefix)
    
    # YouTube başlığı ve açıklaması
    yt_title = f"{title_prefix} | İlginç Bir Hikaye #shorts"
    description = f"{text[:80]}...\n\nDevamı videoda! Abone olmayı unutmayın.\n\n#shorts #{topic.lower()} #kesfet"
    
    upload_to_youtube(video_file, yt_title, description, topic)

if __name__ == "__main__":
    main()
