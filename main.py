import os
import random
import json
import requests
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
    "Sıcak su, soğuk sudan daha hızlı donar. Buna Mpemba etkisi denir.",
    "Jüpiter ve Satürn'de elmas yağmurları yağar.",
    "Kutup ayılarının derisi aslında siyahtır, tüyleri ise şeffaftır.",
    "Muz bitkisi ağaç değil, dünyanın en büyük otudur."
]

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        raise ValueError("TOKEN_JSON bulunamadı! GitHub Secrets kontrol et.")
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

def download_background():
    # Telifsiz ücretsiz bir arka plan videosu (Uzay temalı)
    url = "https://videos.pexels.com/video-files/3129957/3129957-hd_1080_1920_25fps.mp4"
    if not os.path.exists("background.mp4"):
        print("Arka plan videosu indiriliyor...")
        r = requests.get(url)
        with open("background.mp4", 'wb') as f:
            f.write(r.content)
        print("İndirme tamamlandı.")

def create_video(text):
    print(f"Video hazırlanıyor: {text}")
    
    # 1. Sesi Oluştur
    tts = gTTS(text, lang='tr')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. Arka Planı Hazırla
    download_background()
    background = VideoFileClip("background.mp4")
    
    # Videoyu ses süresine göre kes (fazlasını at)
    # Shorts için max 60 saniye, ama ses ne kadarsa o kadar olsun.
    video = background.subclip(0, audio.duration + 1)
    video = video.set_audio(audio)
    
    # 3. Yazıyı Ekle
    # Basit bir yazı ekliyoruz, ortalanmış.
    # Not: Türkçe karakter sorunu olmaması için fontu None bırakıyoruz veya destekleyen font lazım.
    txt_clip = TextClip(text, fontsize=50, color='white', bg_color='black', 
                        size=(video.w * 0.8, None), method='caption')
    txt_clip = txt_clip.set_pos('center').set_duration(video.duration)
    
    # 4. Birleştir
    final_video = CompositeVideoClip([video, txt_clip])
    final_video.write_videofile("shorts_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "shorts_video.mp4"

def upload_to_youtube(file_path, title, description):
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["shorts", "ilgincbilgiler", "bilgi", "bunubiliyormuydun"],
                "categoryId": "27" # Eğitim kategorisi
            },
            "status": {
                "privacyStatus": "public", # Direkt yayına al (veya 'private' yapıp sen onayla)
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(file_path)
    )
    response = request.execute()
    print(f"YÜKLEME BAŞARILI! Video ID: {response['id']}")

def main():
    try:
        # Rastgele bir bilgi seç
        fact = random.choice(FACTS)
        
        # Videoyu oluştur
        video_file = create_video(fact)
        
        # YouTube'a yükle
        title = f"Bunu Biliyor muydunuz? #shorts #bilgi"
        description = f"İlginç bilgiler: {fact}\n\nAbone olmayı unutmayın!"
        
        upload_to_youtube(video_file, title, description)
        
    except Exception as e:
        print(f"HATA OLUŞTU: {e}")

if __name__ == "__main__":
    main()
