import os
import random
import json
import requests
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# --- AYARLAR ---
FACTS = [
    "Bal bozulmayan tek yiyecektir. 3000 yıllık bal bile yenebilir.",
    "Ahtapotların üç kalbi vardır.",
    "Zürafaların ses telleri yoktur.",
    "Dünyadaki insanların toplam ağırlığı, karıncaların toplam ağırlığına eşittir.",
    "Bir insan hayatı boyunca ortalama 22 kilogram deri döker.",
    "Venüs gezegeninde bir gün, bir yıldan daha uzundur.",
    "Sıcak su, soğuk sudan daha hızlı donar.",
    "Jüpiter ve Satürn'de elmas yağmurları yağar."
]

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        print("HATA: TOKEN_JSON bulunamadı!")
        sys.exit(1)
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

def download_background():
    # 1. SAĞLAM LİNK (Pexels - Dikey Video)
    url = "https://videos.pexels.com/video-files/5977735/5977735-uhd_2160_3840_25fps.mp4"
    
    # Bot olduğumuzu gizlemek için kimlik (Header) ekliyoruz
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("Arka plan videosu indiriliyor...")
    try:
        r = requests.get(url, headers=headers, stream=True)
        r.raise_for_status()
        with open("background.mp4", 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("İndirme başarılı!")
    except Exception as e:
        print(f"Video indirilemedi: {e}")
        sys.exit(1)

def create_video(text):
    print(f"Video hazırlanıyor: {text}")
    
    # 1. Sesi Oluştur
    tts = gTTS(text, lang='tr')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. Arka Planı Hazırla
    download_background()
    
    # Dosya boyutu kontrolü (Boş inerse hata verelim)
    if os.path.getsize("background.mp4") < 1000:
        print("HATA: İndirilen video dosyası boş!")
        sys.exit(1)

    try:
        background = VideoFileClip("background.mp4")
        
        # Videoyu ses süresine göre kes
        video = background.subclip(0, audio.duration + 1.5)
        video = video.set_audio(audio)
        
        # 3. Yazıyı Ekle
        # Basit, beyaz renkli, ortalanmış yazı
        # Font sorununu önlemek için varsayılan fontu kullanıyoruz
        txt_clip = TextClip(text, fontsize=50, color='white', bg_color='black', 
                            size=(video.w * 0.9, None), method='caption')
        txt_clip = txt_clip.set_pos('center').set_duration(video.duration)
        
        # 4. Birleştir
        final_video = CompositeVideoClip([video, txt_clip])
        final_video.write_videofile("shorts_video.mp4", fps=24, codec="libx264", audio_codec="aac")
        return "shorts_video.mp4"
        
    except Exception as e:
        print(f"Video işleme hatası: {e}")
        sys.exit(1)

def upload_to_youtube(file_path, title, description):
    try:
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        
        print("YouTube'a yükleniyor...")
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["shorts", "bilgi", "ilginc"],
                    "categoryId": "27"
                },
                "status": {
                    "privacyStatus": "public", 
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(file_path)
        )
        response = request.execute()
        print(f"✅ YÜKLEME BAŞARILI! Video ID: {response['id']}")
    except Exception as e:
        print(f"YouTube Yükleme Hatası: {e}")
        sys.exit(1)

def main():
    fact = random.choice(FACTS)
    video_file = create_video(fact)
    
    title = f"Bunları Biliyor muydun? 😲 #shorts"
    description = f"İlginç bilgiler: {fact}\n\n#shorts #bilgi"
    
    upload_to_youtube(video_file, title, description)

if __name__ == "__main__":
    main()

