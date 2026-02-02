import os
import random
import requests
from openai import OpenAI
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

# API TANIMLAMALARI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def icerik_uret():
    # 1. Senaryo Üret
    print("Senaryo yazılıyor...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Bana 'Biliyor muydunuz?' tarzında, çok ilginç, şaşırtıcı ve az bilinen bir gerçek hakkında 1 cümlelik bir YouTube Shorts metni yaz. Sadece metni ver."}]
    )
    text = response.choices[0].message.content
    print(f"Metin: {text}")

    # 2. Ses Üret (TTS)
    print("Seslendiriliyor...")
    speech_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    speech_response.stream_to_file("audio.mp3")

    # 3. Görsel Üret (DALL-E)
    print("Görsel çiziliyor...")
    img_response = client.images.generate(
        model="dall-e-3",
        prompt=f"Realistic, vertical format style, describing this text visually: {text}",
        size="1024x1792",
        quality="standard",
        n=1,
    )
    image_url = img_response.data[0].url
    img_data = requests.get(image_url).content
    with open('image.png', 'wb') as handler:
        handler.write(img_data)
        
    return text

def video_birlestir():
    print("Video montajlanıyor...")
    # Ses dosyasını yükle
    audio_clip = AudioFileClip("audio.mp3")
    
    # Görseli yükle ve süresini ses kadar yap
    image_clip = ImageClip("image.png").set_duration(audio_clip.duration + 1)
    
    # Basit bir zoom efekti veya statik video (Hata almamak için şimdilik statik)
    video = image_clip.set_audio(audio_clip)
    
    # Dosyayı kaydet
    video.write_videofile("shorts_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("Video hazır!")

def youtube_yukle(baslik):
    print("YouTube'a yükleniyor...")
    
    # Token'ı GitHub Secret'tan alıp json dosyasına çeviriyoruz
    token_info = json.loads(os.environ.get("YOUTUBE_TOKEN_JSON"))
    creds = Credentials.from_authorized_user_info(token_info)

    youtube = build('youtube', 'v3', credentials=creds)

    request_body = {
        'snippet': {
            'title': f"{baslik} #Shorts",
            'description': 'AI tarafından üretilmiştir.',
            'tags': ['shorts', 'ai', 'facts'],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public', # Test ederken 'private' yapabilirsin
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload('shorts_video.mp4', chunksize=-1, resumable=True)
    
    response = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media
    ).execute()

    print(f"Yüklendi! Video ID: {response.get('id')}")

if __name__ == "__main__":
    konu_basligi = icerik_uret()
    video_birlestir()
    youtube_yukle(konu_basligi)

