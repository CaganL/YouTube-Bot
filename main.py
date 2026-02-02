import os
import random
import json
import requests
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip

# --- AYARLAR ---
FACTS = [
    "Bal bozulmayan tek yiyecektir.",
    "Ahtapotların üç kalbi vardır.",
    "Zürafaların ses telleri yoktur.",
    "Dünyadaki insanların toplam ağırlığı karıncalara eşittir.",
    "Bir insan hayatı boyunca 22 kg deri döker.",
    "Venüs'te bir gün bir yıldan uzundur.",
    "Sıcak su soğuk sudan hızlı donar.",
    "Jüpiter'de elmas yağmurları yağar."
]

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        print("HATA: TOKEN_JSON bulunamadı!")
        sys.exit(1)
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

def download_background():
    # Farklı bir kaynak deniyoruz (Daha basit bir video)
    url = "https://www.w3schools.com/html/mov_bbb.mp4" 
    
    print("Arka plan videosu indiriliyor...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, stream=True, timeout=10)
        r.raise_for_status()
        with open("background.mp4", 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("İndirme başarılı!")
        return True
    except Exception as e:
        print(f"Video indirilemedi (Sorun değil, renkli arka plan yapılacak): {e}")
        return False

def create_video(text):
    print(f"Video hazırlanıyor: {text}")
    
    # 1. Sesi Oluştur
    tts = gTTS(text, lang='tr')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. Arka Planı Hazırla
    download_success = download_background()
    
    if download_success and os.path.exists("background.mp4"):
        # Video indiyse onu kullan
        background = VideoFileClip("background.mp4")
        # Dikey (Shorts) formatına zorla: Ortadan kes
        background = background.crop(x1=background.w/2 - 300, y1=0, width=600, height=background.h)
        background = background.resize(height=1920) # Yüksekliği ayarla
        background = background.crop(x1=background.w/2 - 540, width=1080, height=1920) # Tam 1080x1920 yap
    else:
        # Video inemediyse SİYAH ekran kullan (Hata vermesin diye)
        print("Yedek plan devreye girdi: Siyah arka plan oluşturuluyor.")
        background = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=audio.duration + 2)
    
    # Videoyu ses süresine göre ayarla
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    # 3. Yazıyı Ekle
    txt_clip = TextClip(text, fontsize=70, color='white', bg_color='transparent', 
                        size=(900, None), method='caption')
    txt_clip = txt_clip.set_pos('center').set_duration(video.duration)
    
    # 4. Birleştir
    final_video = CompositeVideoClip([video, txt_clip])
    final_video.write_videofile("shorts_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "shorts_video.mp4"

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
    try:
        fact = random.choice(FACTS)
        video_file = create_video(fact)
        
        title = f"Bunları Biliyor muydun? 🚀 #shorts"
        description = f"İlginç bilgiler: {fact}\n\n#shorts #bilgi"
        
        upload_to_youtube(video_file, title, description)
    except Exception as e:
        print(f"Genel Hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

