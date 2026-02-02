import os
import random
import json
import sys
import asyncio
import edge_tts
import textwrap
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx, CompositeAudioClip
from moviepy.audio.fx.all import volumex

# --- HİKAYE VE ARAMA TERİMLERİ ---
STORIES = [
    {
        "topic": "KORKU",
        "search_query": "scary forest fog dark spooky", # Pexels'te ne arayacak?
        "title": "😱 GECE YARISI MİSAFİRİ",
        "text": "Japon efsanesi Kuchisake-onna'ya göre, gece sisli bir sokakta yürürken maskeli bir kadın karşınıza çıkıp 'Ben güzel miyim?' diye sorarsa, sakın cevap vermeyin. 'Evet' derseniz maskesini çıkarır, yırtık ağzını gösterir ve 'Peki ya şimdi?' diye bağırır. 'Hayır' derseniz ise... Sizi oracıkta cezalandırır."
    },
    {
        "topic": "BILGI",
        "search_query": "space galaxy planet stars abstract",
        "title": "🪐 VENÜS'ÜN TUHAF ZAMANI",
        "text": "Güneş sistemimizin en sıcak gezegeni Venüs'te zaman kavramı tam bir kaostur. Venüs kendi etrafında o kadar yavaş döner ki, bir Venüs günü, Dünya'daki 243 güne eşittir. Yani Venüs'te yaşıyor olsaydınız, doğum gününüzü her gün kutlayabilirdiniz!"
    },
    {
        "topic": "DENIZ",
        "search_query": "ocean waves storm underwater dark sea",
        "title": "🌊 OKYANUSUN GÜCÜ",
        "text": "Okyanuslar o kadar devasa ve derindir ki, insanlık olarak bizler sadece %5'ini keşfedebildik. Eğer şu an Dünya'daki 8 milyar insanın tamamı aynı anda okyanusa atlasaydı, su seviyesi sadece bir saç teli kalınlığı kadar yükselirdi. Okyanusun yanında biz bir hiçiz."
    },
    {
        "topic": "GIZEM",
        "search_query": "dark corridor shadow horror mystery",
        "title": "🚫 O SESİ SAKIN DİNLEME",
        "text": "Evinizde yalnızken, boş bir odadan kendi isminizin fısıldandığını duyarsanız ne yaparsınız? Sakın 'Efendim?' demeyin. Eski inanışlara göre, bu tanıdık sesler aslında birer tuzaktır. Kötü niyetli varlıklar, güveninizi kazanmak için sevdiklerinizin sesini taklit eder."
    },
    {
        "topic": "ILGINC",
        "search_query": "dna microscopic science abstract cell",
        "title": "🍌 DNA BENZERLİĞİ",
        "text": "Kendinizi çok özel hissediyor musunuz? İnsan DNA'sı ile bir muzun DNA'sı %50 oranında birebir aynıdır. Yani genetik olarak yarı yarıya bir meyveyle akrabasınız. Doğanın mizah anlayışı gerçekten inanılmaz."
    }
]

# --- API AYARLARI ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    return Credentials.from_authorized_user_info(json.loads(token_json))

async def generate_pro_voice(text, filename="voice.mp3"):
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="+5%", pitch="-5Hz")
    await communicate.save(filename)

# --- YENİ VİDEO BULUCU (API İLE) ---
def download_video_from_pexels(query):
    if not PEXELS_API_KEY:
        print("🚨 HATA: PEXELS_API_KEY bulunamadı! Lütfen Secret ekleyin.")
        return None
    
    print(f"🌍 Pexels'te aranıyor: {query}")
    headers = {"Authorization": PEXELS_API_KEY}
    # Dikey (Portrait) videoları ara
    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        
        if "videos" in data and len(data["videos"]) > 0:
            # Rastgele bir video seç (Hep aynısı olmasın diye)
            video_data = random.choice(data["videos"])
            video_files = video_data["video_files"]
            
            # En uygun kaliteyi bul (HD ama çok büyük olmayan)
            best_link = None
            for v in video_files:
                # 720p veya 1080p ve dikey olanı al
                if v["height"] >= 1280 and v["width"] < v["height"]:
                    best_link = v["link"]
                    break
            
            if not best_link: best_link = video_files[0]["link"] # Bulamazsa ilkini al
            
            # İndir
            print("📥 Video indiriliyor...")
            vid_r = requests.get(best_link, stream=True)
            with open("downloaded_bg.mp4", "wb") as f:
                for chunk in vid_r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            return "downloaded_bg.mp4"
            
    except Exception as e:
        print(f"Pexels Hatası: {e}")
        return None

# --- RASTGELE MÜZİK SEÇİCİ ---
def get_random_music(topic):
    # Klasördeki tüm dosyaları tara
    all_files = os.listdir(".")
    # Konuya uygun müzikleri filtrele (örn: dosya adı 'korku' içeriyorsa)
    matching_music = [f for f in all_files if f.endswith(".mp3") and topic.lower() in f.lower()]
    
    # Eğer o konuda müzik yoksa, herhangi bir mp3 seç
    if not matching_music:
        matching_music = [f for f in all_files if f.endswith(".mp3") and "voice.mp3" not in f]
    
    if matching_music:
        selected = random.choice(matching_music)
        print(f"🎵 Seçilen Müzik: {selected}")
        return selected
    return None

def create_dynamic_subtitles(text, audio_duration):
    sentences = text.replace("?", ".").replace("!", ".").split(". ")
    sentences = [s.strip() + "." for s in sentences if s.strip()]
    sentence_duration = audio_duration / len(sentences)
    clips = []
    current_time = 0
    for sentence in sentences:
        wrapped_text = "\n".join(textwrap.wrap(sentence, width=25))
        txt_clip = TextClip(wrapped_text, fontsize=55, color='white', font='Arial-Bold',
                            stroke_color='black', stroke_width=3, method='caption', 
                            align='center', size=(900, None))
        txt_clip = txt_clip.set_start(current_time).set_duration(sentence_duration).set_pos(('center', 1300))
        clips.append(txt_clip)
        current_time += sentence_duration
    return clips

def create_final_video(story_data):
    print(f"🎬 Video İşleniyor: {story_data['title']}")
    
    # 1. Ses
    asyncio.run(generate_pro_voice(story_data['text']))
    voice_audio = AudioFileClip("voice.mp3")
    
    # 2. Video (API'den indir)
    video_path = download_video_from_pexels(story_data["search_query"])
    if not video_path:
        # API çalışmazsa yedek (varsa)
        if os.path.exists("background.mp4"): video_path = "background.mp4"
        else: sys.exit("Video bulunamadı!")
        
    background = VideoFileClip(video_path)
    if background.w > background.h: 
        background = background.crop(x_center=background.w/2, width=background.h*9/16, height=background.h)
    background = background.resize(height=1920).crop(x_center=background.w/2, width=1080, height=1920)
    background = background.fx(vfx.loop, duration=voice_audio.duration + 2)

    # 3. Müzik
    music_file = get_random_music(story_data["topic"])
    if music_file:
        music_audio = AudioFileClip(music_file).fx(vfx.loop, duration=voice_audio.duration + 2)
        music_audio = music_audio.fx(volumex, 0.15)
        final_audio = CompositeAudioClip([voice_audio, music_audio])
    else:
        final_audio = voice_audio

    video = background.set_duration(voice_audio.duration + 1.5)
    video = video.set_audio(final_audio)
    
    # 4. Altyazı ve Başlık
    title_clip = TextClip(story_data['title'], fontsize=70, color='white', bg_color='#cc0000', 
                        size=(900, None), method='caption', align='center')
    title_clip = title_clip.set_pos(('center', 150)).set_duration(video.duration)
    
    subtitle_clips = create_dynamic_subtitles(story_data['text'], voice_audio.duration)
    
    final_video = CompositeVideoClip([video, title_clip] + subtitle_clips)
    final_video.write_videofile("shorts_video.mp4", fps=30, bitrate="12000k", codec="libx264", audio_codec="aac", preset='medium')
    return "shorts_video.mp4"

def upload_to_youtube(file_path, story_data):
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{story_data['title']} #shorts",
                "description": f"{story_data['text'][:100]}...\n\nAbone ol: @GolgeArsiviTR\n\n#shorts #{story_data['topic'].lower()}",
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload(file_path)
    ).execute()
    print("✅ Yüklendi!")

def main():
    story_data = random.choice(STORIES)
    create_final_video(story_data)
    upload_to_youtube("shorts_video.mp4", story_data)

if __name__ == "__main__":
    main()

