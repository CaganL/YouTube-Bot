import os
import random
import json
import requests
import sys
import asyncio
import edge_tts  # YENİ SES MOTORU
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx, ColorClip

# --- HAFTALIK YAYIN AKIŞI (Takvim) ---
SCHEDULE = {
    "Monday": {"topic": "KORKU", "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4"}, # Karanlık orman
    "Tuesday": {"topic": "BILGI", "video": "https://videos.pexels.com/video-files/856193/856193-hd_1920_1080_24fps.mp4"}, # Uzay/Teknoloji
    "Wednesday": {"topic": "MOTIVASYON", "video": "https://videos.pexels.com/video-files/3326656/3326656-hd_1920_1080_30fps.mp4"}, # Doğa/Deniz
    "Thursday": {"topic": "BILGI", "video": "https://videos.pexels.com/video-files/854898/854898-hd_1920_1080_25fps.mp4"}, # Şehir/Trafik
    "Friday": {"topic": "GIZEM", "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4"},
    "Saturday": {"topic": "EGZOTIK", "video": "https://videos.pexels.com/video-files/4058447/4058447-hd_1080_1920_25fps.mp4"}, # Hayvanlar/Doğa
    "Sunday": {"topic": "GENEL", "video": "https://videos.pexels.com/video-files/856193/856193-hd_1920_1080_24fps.mp4"}
}

# --- İÇERİK HAVUZU (Gemini bağlanana kadar burası) ---
CONTENT_POOL = {
    "KORKU": [
        "1980'lerde bir kasabada tüm televizyonlar aynı anda kapandı. Ekranlarda sadece 'Arkanıza bakmayın' yazısı belirdi. O gece kasabada 50 kişi kayboldu ve bir daha asla bulunamadı.",
        "Japonya'da kiralık bir daire tutan öğrenci, duvardaki küçük delikten yan daireyi izliyordu. Tek gördüğü kırmızılıktı. Ev sahibine sordu. Ev sahibi 'Orada hasta bir kadın yaşıyor, gözleri kırmızıdır' dedi."
    ],
    "BILGI": [
        "Balinalar okyanusun dibinde şarkı söylerken sesleri o kadar güçlüdür ki, bu ses dalgaları 1000 kilometre öteden duyulabilir. Bir jet uçağından daha gürültülüdürler.",
        "Eğer bir kağıdı 42 kez katlayabilseydiniz, kalınlığı Ay'a kadar ulaşırdı. Ancak fiziksel olarak bir kağıdı 7 kereden fazla katlamak neredeyse imkansızdır."
    ],
    "MOTIVASYON": [
        "Vazgeçtiğin an, aslında başarmaya en yakın olduğun andır. Tıpkı gecenin en karanlık anının, şafaktan hemen öncesi olması gibi. Devam et.",
        "Bugün ektiğin tohumlar, yarın gölgesinde oturacağın ağaçlar olacak. Yorulsan da durma."
    ],
    "GIZEM": [
        "Voynich el yazması, 600 yıldır kimsenin çözemediği bir dilde yazılmıştır. Kitaptaki bitkilerin hiçbiri dünyada bulunmamaktadır.",
        "Bermuda Şeytan Üçgeni'nde pusulalar kuzeyi göstermez. Manyetik alanın orada neden bozulduğunu bilim insanları hala tam olarak açıklayamıyor."
    ],
    "EGZOTIK": [
        "Bukalemunların dilleri, vücutlarının iki katı uzunluğundadır ve bir jet uçağından daha hızlı fırlarlar.",
        "Ahtapotların kollarında kendi beyinleri vardır. Bir kol kopsa bile hareket etmeye ve avlanmaya çalışır."
    ],
    "GENEL": [
        "Tarihteki en kısa savaş sadece 38 dakika sürmüştür. İngiltere ve Zanzibar arasında geçen savaşta Zanzibar 38. dakikada teslim olmuştur."
    ]
}

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

# --- YENİ PROFESYONEL SES FONKSİYONU ---
async def generate_pro_voice(text, filename="voice.mp3"):
    # "tr-TR-AhmetNeural" (Erkek) veya "tr-TR-EmelNeural" (Kadın) seçebilirsin
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save(filename)

def create_video_pro(text, background_url, topic):
    print(f"🎬 PRO Video hazırlanıyor... Konu: {topic}")
    
    # 1. Profesyonel Sesi Oluştur
    asyncio.run(generate_pro_voice(text))
    audio = AudioFileClip("voice.mp3")
    print(f"🎙️ Ses hazır! Süre: {audio.duration} sn")
    
    # 2. Kaliteli Arka Plan İndir
    print("📥 4K Video indiriliyor...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(background_url, headers=headers, stream=True)
    with open("background.mp4", 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
            
    background = VideoFileClip("background.mp4")
    
    # 3. Görüntü Ayarları (Dikey ve Loop)
    # Eğer video yataysa, ortadan dikey kes
    if background.w > background.h:
        # Tam ortadan 1080x1920 oranında kes
        target_ratio = 9/16
        new_width = background.h * target_ratio
        crop_x = (background.w - new_width) / 2
        background = background.crop(x1=crop_x, width=new_width, height=background.h)
    
    background = background.resize(height=1920) # Yüksekliği 1920'ye sabitle
    background = background.crop(x1=background.w/2 - 540, width=1080, height=1920) # 1080 genişlik garanti
    
    # Loop (Döngü)
    background = background.fx(vfx.loop, duration=audio.duration + 1.5)
    
    # 4. Sesi Birleştir
    video = background.set_audio(audio)
    
    # 5. Yazı (Daha Profesyonel Font ve Konum)
    # Altyazıyı sarı ve siyah gölgeli yapalım
    # Not: Türkçe karakter sorunu olmasın diye basit karakterler seçilebilir veya font yüklenmeli.
    # Şimdilik temiz beyaz.
    txt_clip = TextClip("SONUNA KADAR IZLE!", fontsize=70, color='white', bg_color='red', 
                        size=(800, None), method='caption')
    txt_clip = txt_clip.set_pos(('center', 200)).set_duration(video.duration)
    
    # 6. Render (Yüksek Kalite)
    final_video = CompositeVideoClip([video, txt_clip])
    # bitrate="5000k" ile kaliteyi artırıyoruz
    final_video.write_videofile("shorts_video.mp4", fps=30, bitrate="6000k", codec="libx264", audio_codec="aac")
    return "shorts_video.mp4"

def upload_to_youtube(file_path, title, description, category_id="27"):
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["shorts", "kesfet", "ilginc"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(file_path)
    ).execute()
    print("✅ YÜKLEME TAMAMLANDI!")

def main():
    # 1. Bugün Günlerden Ne?
    day_name = datetime.now().strftime("%A") # Monday, Tuesday...
    print(f"📅 Bugün günlerden: {day_name}")
    
    # 2. Programa göre konu seç
    schedule_info = SCHEDULE.get(day_name, SCHEDULE["Sunday"]) # Bulamazsa Pazar'ı kullan
    topic = schedule_info["topic"]
    bg_video_url = schedule_info["video"]
    
    # 3. O konudan rastgele bir metin seç
    text = random.choice(CONTENT_POOL.get(topic, CONTENT_POOL["GENEL"]))
    
    # 4. Video Yap
    video_file = create_video_pro(text, bg_video_url, topic)
    
    # 5. Başlık Oluştur
    title = f"{topic} ZAMANI! 😱 #shorts"
    desc = f"Günün {topic} içerigi: {text[:50]}...\n\n#shorts #{topic.lower()}"
    
    # 6. Yükle
    upload_to_youtube(video_file, title, desc)

if __name__ == "__main__":
    main()
