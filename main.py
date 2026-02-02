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

# --- AYARLAR ---
SCHEDULE = {
    "Monday": {"topic": "KORKU", "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4"},
    "Tuesday": {"topic": "BILGI", "video": "https://videos.pexels.com/video-files/856193/856193-hd_1920_1080_24fps.mp4"},
    "Wednesday": {"topic": "MOTIVASYON", "video": "https://videos.pexels.com/video-files/3326656/3326656-hd_1920_1080_30fps.mp4"},
    "Thursday": {"topic": "BILGI", "video": "https://videos.pexels.com/video-files/854898/854898-hd_1920_1080_25fps.mp4"},
    "Friday": {"topic": "GIZEM", "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4"},
    "Saturday": {"topic": "EGZOTIK", "video": "https://videos.pexels.com/video-files/4058447/4058447-hd_1080_1920_25fps.mp4"},
    "Sunday": {"topic": "GENEL", "video": "https://videos.pexels.com/video-files/856193/856193-hd_1920_1080_24fps.mp4"}
}

CONTENT_POOL = {
    "KORKU": [
        "1980'lerde bir kasabada tüm televizyonlar aynı anda kapandı. Ekranlarda sadece 'Arkanıza bakmayın' yazısı belirdi. O gece 50 kişi kayboldu.",
        "Evinizdeyken isminizin çağrıldığını duyarsanız sakın cevap vermeyin. Bazı inanışlara göre bu, sizi diğer tarafa çekmeye çalışan bir davettir."
    ],
    "BILGI": [
        "Balinaların şarkıları okyanus altında bir jet uçağından daha yüksek ses çıkarabilir.",
        "İnsan DNA'sı ile muz DNA'sı %50 oranında benzerlik gösterir."
    ],
    "MOTIVASYON": ["Başlamak için mükemmel olmayı bekleme, ama mükemmel olmak için başla.", "Yorulduğunda dinlenmeyi öğren, bırakmayı değil."],
    "GIZEM": ["Voynich el yazması 600 yıldır çözülememiştir.", "Bermuda Şeytan Üçgeni'nde pusulalar sapıtır."],
    "EGZOTIK": ["Ahtapotların üç kalbi vardır.", "Bukalemunların dilleri vücutlarından uzundur."],
    "GENEL": ["Zürafaların ses telleri yoktur.", "Bal bozulmayan tek yiyecektir."]
}

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        print("HATA: TOKEN_JSON bulunamadı!")
        sys.exit(1)
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

async def generate_pro_voice(text, filename="voice.mp3"):
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save(filename)

def create_video_pro(text, background_url, topic):
    print(f"🎬 PRO Video hazırlanıyor... Konu: {topic}")
    
    # 1. Ses
    asyncio.run(generate_pro_voice(text))
    audio = AudioFileClip("voice.mp3")
    
    # 2. Arka Plan İndirme (GÜVENLİ MOD)
    print("📥 Video indiriliyor...")
    video_downloaded = False
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.get(background_url, headers=headers, stream=True, timeout=15)
        if r.status_code == 200:
            with open("background.mp4", 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            # Dosya boyutu kontrolü (100KB'dan küçükse bozuktur)
            if os.path.getsize("background.mp4") > 100000:
                video_downloaded = True
            else:
                print("⚠️ İndirilen dosya çok küçük (Bozuk).")
    except Exception as e:
        print(f"⚠️ İndirme hatası: {e}")

    # 3. Video İşleme
    if video_downloaded:
        try:
            background = VideoFileClip("background.mp4")
            # Dikey yap
            if background.w > background.h:
                 background = background.crop(x1=background.w/2 - 270, width=540, height=960)
            background = background.resize(height=1920)
            background = background.crop(x1=background.w/2 - 540, width=1080, height=1920)
            # Loop
            background = background.fx(vfx.loop, duration=audio.duration + 1.5)
        except Exception as e:
            print(f"⚠️ Video işleme hatası: {e}. Yedek plana geçiliyor.")
            video_downloaded = False

    # EĞER VİDEO BOZUKSA -> SİYAH EKRAN KULLAN (Çökmemesi için)
    if not video_downloaded:
        print("🚨 Yedek Arka Plan Devrede (Siyah Ekran)")
        background = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=audio.duration + 1.5)

    # 4. Birleştir
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    txt_clip = TextClip("SONUNA KADAR IZLE!", fontsize=70, color='white', bg_color='red', 
                        size=(800, None), method='caption')
    txt_clip = txt_clip.set_pos(('center', 250)).set_duration(video.duration)
    
    final_video = CompositeVideoClip([video, txt_clip])
    # Hata almamak için preset='ultrafast' ekledik
    final_video.write_videofile("shorts_video.mp4", fps=24, bitrate="5000k", codec="libx264", audio_codec="aac", preset='ultrafast')
    return "shorts_video.mp4"

def upload_to_youtube(file_path, title, description):
    try:
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["shorts", "kesfet"],
                    "categoryId": "27"
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(file_path)
        )
        response = request.execute()
        print(f"✅ YÜKLEME BAŞARILI! Video ID: {response['id']}")
    except Exception as e:
        print(f"YouTube Hatası: {e}")
        sys.exit(1)

def main():
    day_name = datetime.now().strftime("%A")
    schedule = SCHEDULE.get(day_name, SCHEDULE["Sunday"])
    text = random.choice(CONTENT_POOL.get(schedule["topic"], CONTENT_POOL["GENEL"]))
    
    video_file = create_video_pro(text, schedule["video"], schedule["topic"])
    
    title = f"{schedule['topic']} ZAMANI! 😱 #shorts"
    upload_to_youtube(video_file, title, title)

if __name__ == "__main__":
    main()
