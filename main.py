import os
import random
import json
import sys
import asyncio
import edge_tts
import textwrap
import requests
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx, CompositeAudioClip
from moviepy.audio.fx.all import volumex

# --- İÇERİK HAVUZU ---
STORIES = [
    {"topic": "KORKU", "search_query": "dark spooky forest fog", "title": "😱 GECE YARISI MİSAFİRİ", "text": "Japon efsanesi Kuchisake-onna'ya göre, gece sisli bir sokakta yürürken maskeli bir kadın karşınıza çıkıp 'Ben güzel miyim?' diye sorarsa, sakın cevap vermeyin. 'Evet' derseniz maskesini çıkarır, yırtık ağzını gösterir ve 'Peki ya şimdi?' diye bağırır. Hayır derseniz ise... Sizi cezalandırır."},
    {"topic": "BILGI", "search_query": "space galaxy cinematic stars", "title": "🪐 VENÜS'ÜN TUHAF ZAMANI", "text": "Güneş sistemimizin en sıcak gezegeni Venüs'te zaman kavramı tam bir kaostur. Venüs kendi etrafında o kadar yavaş döner ki, bir Venüs günü, Dünya'daki 243 güne eşittir. Ancak Güneş etrafındaki turunu 225 günde tamamlar. Yani Venüs'te bir gün, bir yıldan daha uzundur!"},
    {"topic": "DENIZ", "search_query": "deep ocean waves cinematic", "title": "🌊 OKYANUSUN GÜCÜ", "text": "Okyanuslar o kadar devasa ve derindir ki, insanlık olarak sadece yüzde beşini keşfedebildik. Eğer şu an dünyadaki sekiz milyar insanın tamamı aynı anda okyanusa atlasaydı, su seviyesi sadece bir saç teli kalınlığı kadar yükselirdi. Okyanusun yanında biz bir hiçiz."}
]

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        print("🚨 HATA: TOKEN_JSON bulunamadı! Secret eklenmemiş olabilir.")
        sys.exit(1)
    return Credentials.from_authorized_user_info(json.loads(token_json))

async def generate_pro_voice(text, filename="voice.mp3"):
    print("🎙️ Ses oluşturuluyor...")
    try:
        communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="+10%", pitch="-5Hz")
        await communicate.save(filename)
        print("✅ Ses dosyası hazır.")
    except Exception as e:
        print(f"🚨 SES HATASI: {e}")
        sys.exit(1)

def download_video_from_pexels(query):
    if not PEXELS_API_KEY:
        print("🚨 HATA: PEXELS_API_KEY bulunamadı! Secret'ları kontrol et.")
        sys.exit(1)
    
    print(f"🌍 Pexels'te aranıyor: {query}")
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"🚨 PEXELS API HATASI: {r.status_code} - {r.text}")
            sys.exit(1)
            
        data = r.json()
        if "videos" in data and len(data["videos"]) > 0:
            video_data = random.choice(data["videos"])
            best_link = video_data["video_files"][0]["link"]
            print(f"📥 Video bulundu, indiriliyor... (ID: {video_data['id']})")
            
            vid_r = requests.get(best_link, stream=True)
            with open("downloaded_bg.mp4", "wb") as f:
                for chunk in vid_r.iter_content(chunk_size=1024*1024): f.write(chunk)
            
            if os.path.getsize("downloaded_bg.mp4") < 1000:
                print("🚨 HATA: İnen video dosyası bozuk veya boş!")
                sys.exit(1)
                
            return "downloaded_bg.mp4"
        else:
            print("🚨 HATA: Bu konuda hiç video bulunamadı!")
            sys.exit(1)
    except Exception as e:
        print(f"🚨 İNDİRME HATASI: {e}")
        sys.exit(1)

def main():
    story_data = random.choice(STORIES)
    print(f"🎬 İŞLEM BAŞLIYOR: {story_data['title']}")
    
    # 1. Ses
    asyncio.run(generate_pro_voice(story_data['text']))
    voice_audio = AudioFileClip("voice.mp3")
    
    # 2. Video İndirme
    video_path = download_video_from_pexels(story_data["search_query"])
    # Not: download fonksiyonu hata varsa zaten sys.exit yapacak.
    
    print("🎞️ Video işleniyor (MoviePy)...")
    background = VideoFileClip(video_path)
    
    # Kırpma İşlemleri
    if background.w > background.h:
        background = background.crop(x_center=background.w/2, width=background.h*9/16, height=background.h)
    background = background.resize(height=1920).crop(x_center=background.w/2, width=1080, height=1920)
    background = background.fx(vfx.loop, duration=voice_audio.duration + 2)
    
    # Ses Birleştirme
    final_audio = voice_audio # Müzik şimdilik devre dışı (Hata kaynağını azaltmak için)
    video = background.set_duration(voice_audio.duration + 1.5).set_audio(final_audio)
    
    # Altyazı ve Başlık
    title_clip = TextClip(story_data['title'], fontsize=70, color='white', bg_color='#cc0000', 
                          size=(900, None), method='caption', align='center')
    title_clip = title_clip.set_pos(('center', 150)).set_duration(video.duration)
    
    # Basit Altyazı (Dinamik yerine statik - hatayı izole etmek için)
    # Eğer bu çalışırsa dinamik olanı geri ekleriz.
    
    output_file = "shorts_video.mp4"
    print("⚙️ Render başlatılıyor...")
    final_video = CompositeVideoClip([video, title_clip])
    final_video.write_videofile(output_file, fps=24, bitrate="5000k", codec="libx264", audio_codec="aac")
    
    # Dosya Kontrolü
    if not os.path.exists(output_file):
        print("🚨 HATA: Render bitti ama dosya oluşmadı!")
        sys.exit(1)
        
    print(f"✅ Video oluşturuldu: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
    
    # 3. Yükleme
    print("🚀 YouTube'a yükleniyor...")
    try:
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"{story_data['title']} #shorts",
                    "description": story_data['text'],
                    "categoryId": "27"
                },
                "status": {
                    "privacyStatus": "public", # Eğer hata verirse 'private' yapıp dene
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(output_file)
        )
        response = request.execute()
        print(f"🎉 BAŞARILI! Video ID: {response['id']}")
        print(f"🔗 Link: https://youtube.com/shorts/{response['id']}")
        
    except Exception as e:
        print(f"🚨 YOUTUBE YÜKLEME HATASI: {e}")
        # Detaylı hata mesajı için:
        if hasattr(e, 'content'):
            print(f"Detay: {e.content}")
        sys.exit(1)

if __name__ == "__main__":
    main()

