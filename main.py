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

# --- HİKAYE VE VİDEO EŞLEŞTİRMELERİ ---
# Her hikayenin yanına ona uygun video linkini koyduk.
# Böylece "Okyanus" anlatırken ekranda "Orman" olmayacak.

STORIES = [
    {
        "topic": "KORKU",
        "title": "😱 GECE YARISI MİSAFİRİ",
        "text": "Japon efsanesi Kuchisake-onna'ya göre, gece sokakta maskeli bir kadın size 'Ben güzel miyim?' diye sorarsa sakın cevap vermeyin. Evet derseniz maskesini çıkarır ve 'Peki ya şimdi?' diye bağırır. Hayır derseniz... Sonuç hiç iyi olmaz.",
        "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4" # Sisli Sokak/Orman
    },
    {
        "topic": "BILGI",
        "title": "🪐 VENÜS'ÜN SIRRI",
        "text": "Venüs gezegeninde bir gün, bir yıldan daha uzundur. Çünkü Venüs kendi etrafında o kadar yavaş döner ki, Güneş etrafındaki turunu tamamlaması, kendi etrafındaki dönüşünden daha kısa sürer. Yani orada doğdsaydınız, doğum gününüz her gün olurdu.",
        "video": "https://videos.pexels.com/video-files/3129671/3129671-hd_1080_1920_30fps.mp4" # Uzay/Gezegen
    },
    {
        "topic": "DENIZ",
        "title": "🌊 OKYANUSUN GÜCÜ",
        "text": "Eğer Dünya'daki tüm insanlar aynı anda okyanusa girseydi, su seviyesi sadece bir saç teli kalınlığı kadar yükselirdi. Okyanuslar o kadar devasa ve derindir ki, biz insanlar onun büyüklüğü yanında sadece bir hiçiz.",
        "video": "https://videos.pexels.com/video-files/1536322/1536322-hd_1080_1920_30fps.mp4" # Dalgalar
    },
    {
        "topic": "KORKU",
        "title": "🚫 SAKIN CEVAP VERME",
        "text": "Evinizdeyken, boş bir odadan isminizin çağrıldığını duyarsanız sakın 'Efendim' demeyin veya o odaya gitmeyin. Bazı eski inanışlara göre bu ses, kötü niyetli varlıkların sizi kendi boyutlarına çekmek için kullandığı en eski tuzaktır.",
        "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4" # Karanlık Koridor
    }
]

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        sys.exit(1)
    return Credentials.from_authorized_user_info(json.loads(token_json))

# Ses Ayarı: Daha hızlı ve doğal
async def generate_pro_voice(text, filename="voice.mp3"):
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="+10%", pitch="-2Hz")
    await communicate.save(filename)

def create_video_matched(story_data):
    print(f"🎬 Video Başlıyor: {story_data['title']}")
    
    # 1. Ses
    asyncio.run(generate_pro_voice(story_data['text']))
    audio = AudioFileClip("voice.mp3")
    
    # 2. Videoyu İndir (Browser Taklidi Yaparak)
    print("📥 Video indiriliyor...")
    video_downloaded = False
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    
    try:
        r = requests.get(story_data['video'], headers=headers, stream=True, timeout=30)
        if r.status_code == 200:
            with open("background.mp4", 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            if os.path.getsize("background.mp4") > 500000: # 500KB'dan büyükse sağlamdır
                video_downloaded = True
    except Exception as e:
        print(f"Hata: {e}")

    # 3. İşleme
    if not video_downloaded:
        # İnemezse Siyah Ekran (Mecburen)
        background = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=audio.duration + 2)
    else:
        background = VideoFileClip("background.mp4")
        # Dikey Kırpma
        if background.w > background.h:
            new_width = background.h * (9/16)
            background = background.crop(x_center=background.w/2, width=new_width, height=background.h)
        background = background.resize(height=1920)
        background = background.crop(x_center=background.w/2, width=1080, height=1920)
        # Döngü
        background = background.fx(vfx.loop, duration=audio.duration + 2)

    # Birleştir
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    # Başlık
    txt_clip = TextClip(story_data['title'], fontsize=60, color='white', bg_color='#cc0000', 
                        size=(900, None), method='caption', align='center')
    txt_clip = txt_clip.set_pos(('center', 200)).set_duration(video.duration)
    
    final_video = CompositeVideoClip([video, txt_clip])
    final_video.write_videofile("shorts_video.mp4", fps=24, bitrate="5000k", codec="libx264", audio_codec="aac", preset='medium')
    return "shorts_video.mp4"

def upload_to_youtube(file_path, story_data):
    try:
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"{story_data['title']} | İnanılmaz! 😱 #shorts",
                    "description": f"{story_data['text'][:80]}...\n\nAbone ol: @GolgeArsiviTR\n\n#shorts #kesfet #{story_data['topic'].lower()}",
                    "tags": ["shorts", story_data['topic'].lower(), "gizem", "korku"],
                    "categoryId": "27"
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(file_path)
        )
        response = request.execute()
        print(f"✅ YÜKLENDİ! Video ID: {response['id']}")
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)

def main():
    # Listeden rastgele bir hikaye seç
    story_data = random.choice(STORIES)
    
    video_file = create_video_matched(story_data)
    upload_to_youtube(video_file, story_data)

if __name__ == "__main__":
    main()
