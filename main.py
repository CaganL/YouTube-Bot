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
    {"topic": "DENIZ", "search_query": "deep ocean waves cinematic", "title": "🌊 OKYANUSUN GÜCÜ", "text": "Okyanuslar o kadar devasa ve derindir ki, insanlık olarak sadece yüzde beşini keşfedebildik. Eğer şu an dünyadaki sekiz milyar insanın tamamı aynı anda okyanusa atlasaydı, su seviyesi sadece bir saç teli kalınlığı kadar yükselirdi. Okyanusun yanında biz bir hiçiz."},
    {"topic": "ILGINC", "search_query": "science dna laboratory abstract", "title": "🍌 DNA BENZERLİĞİ", "text": "Kendinizi çok özel hissediyor musunuz? İnsan DNA'sı ile bir muzun DNA'sı yüzde elli oranında birebir aynıdır. Yani genetik olarak yarı yarıya bir meyveyle akrabasınız. Doğanın mizah anlayışı gerçekten inanılmaz."}
]

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    return Credentials.from_authorized_user_info(json.loads(token_json))

async def generate_pro_voice(text, filename="voice.mp3"):
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="+10%", pitch="-5Hz")
    await communicate.save(filename)

def download_video_from_pexels(query):
    if not PEXELS_API_KEY: return None
    print(f"🌍 Pexels'te aranıyor: {query}")
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=5"
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        if "videos" in data and len(data["videos"]) > 0:
            video_data = random.choice(data["videos"])
            best_link = video_data["video_files"][0]["link"]
            print("📥 Video indiriliyor...")
            vid_r = requests.get(best_link, stream=True)
            with open("downloaded_bg.mp4", "wb") as f:
                for chunk in vid_r.iter_content(chunk_size=1024*1024): f.write(chunk)
            return "downloaded_bg.mp4"
    except: return None

def get_random_music(topic):
    all_files = os.listdir(".")
    matching_music = [f for f in all_files if f.endswith(".mp3") and topic.lower() in f.lower() and f != "voice.mp3"]
    return random.choice(matching_music) if matching_music else None

def create_dynamic_subtitles(text, audio_duration):
    sentences = text.replace("?", ".").replace("!", ".").split(". ")
    sentences = [s.strip() + "." for s in sentences if s.strip()]
    sentence_duration = audio_duration / len(sentences)
    clips = []
    current_time = 0
    for sentence in sentences:
        wrapped_text = "\n".join(textwrap.wrap(sentence, width=25))
        txt_clip = TextClip(wrapped_text, fontsize=55, color='white', font='Arial-Bold', stroke_color='black', stroke_width=3, method='caption', align='center', size=(900, None))
        txt_clip = txt_clip.set_start(current_time).set_duration(sentence_duration).set_pos(('center', 1300))
        clips.append(txt_clip)
        current_time += sentence_duration
    return clips

def main():
    story_data = random.choice(STORIES)
    print(f"🎬 Video İşleniyor: {story_data['title']}")
    
    asyncio.run(generate_pro_voice(story_data['text']))
    voice_audio = AudioFileClip("voice.mp3")
    
    video_path = download_video_from_pexels(story_data["search_query"])
    if not video_path: return
    
    background = VideoFileClip(video_path)
    if background.w > background.h: 
        background = background.crop(x_center=background.w/2, width=background.h*9/16, height=background.h)
    
    background = background.resize(height=1920).crop(x_center=background.w/2, width=1080, height=1920).fx(vfx.loop, duration=voice_audio.duration + 2)
    
    music_file = get_random_music(story_data["topic"])
    if music_file:
        music_audio = AudioFileClip(music_file).fx(vfx.loop, duration=voice_audio.duration + 2).fx(volumex, 0.15)
        final_audio = CompositeAudioClip([voice_audio, music_audio])
    else: final_audio = voice_audio
    
    video = background.set_duration(voice_audio.duration + 1.5).set_audio(final_audio)
    title_clip = TextClip(story_data['title'], fontsize=70, color='white', bg_color='#cc0000', size=(900, None), method='caption', align='center').set_pos(('center', 150)).set_duration(video.duration)
    subtitle_clips = create_dynamic_subtitles(story_data['text'], voice_audio.duration)
    
    output_file = "shorts_video.mp4"
    final_video = CompositeVideoClip([video, title_clip] + subtitle_clips)
    final_video.write_videofile(output_file, fps=24, bitrate="8000k", codec="libx264", audio_codec="aac")
    
    # Dosyanın oluştuğundan emin olmak için bekleme
    time.sleep(5)
    
    if os.path.exists(output_file):
        print(f"✅ Video hazır, YouTube'a yükleniyor...")
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        youtube.videos().insert(
            part="snippet,status", 
            body={
                "snippet": {"title": f"{story_data['title']} #shorts", "description": story_data['text'], "categoryId": "27"}, 
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            }, 
            media_body=MediaFileUpload(output_file)
        ).execute()
        print("🚀 Başarıyla Yüklendi!")
    else:
        print("🚨 HATA: shorts_video.mp4 oluşturulamadı!")

if __name__ == "__main__": main()

