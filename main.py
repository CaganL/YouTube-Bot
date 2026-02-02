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

# --- GELİŞMİŞ PROGRAM (Linkler Güncellendi) ---
SCHEDULE = {
    "Monday":    {"topic": "KORKU", "title": "😱 KORKU SEANSI", "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4"}, # Sisli Orman (Yedekli)
    "Tuesday":   {"topic": "BILGI", "title": "🧠 BEYİN YAKAN BİLGİ", "video": "https://videos.pexels.com/video-files/3129671/3129671-hd_1080_1920_30fps.mp4"}, # Uzay/Soyut
    "Wednesday": {"topic": "MOTIVASYON", "title": "💪 GÜNÜN MOTİVASYONU", "video": "https://videos.pexels.com/video-files/1536322/1536322-hd_1080_1920_30fps.mp4"}, # Dalgalar
    "Thursday":  {"topic": "BILGI", "title": "🧠 BUNU BİLİYOR MUYDUN?", "video": "https://videos.pexels.com/video-files/3129671/3129671-hd_1080_1920_30fps.mp4"},
    "Friday":    {"topic": "GIZEM", "title": "🕵️‍♂️ GİZEM DOSYALARI", "video": "https://videos.pexels.com/video-files/5435649/5435649-hd_1080_1920_30fps.mp4"},
    "Saturday":  {"topic": "EGZOTIK", "title": "🦜 DOĞANIN MUCİZELERİ", "video": "https://videos.pexels.com/video-files/4549590/4549590-hd_1080_1920_30fps.mp4"}, # Doğa
    "Sunday":    {"topic": "GENEL", "title": "🤔 İLGİNÇ GERÇEKLER", "video": "https://videos.pexels.com/video-files/3129671/3129671-hd_1080_1920_30fps.mp4"}
}

CONTENT_POOL = {
    "KORKU": [
        "Japonya'da, geceleri sokakta yürürken 'Ben güzel miyim?' diye soran maskeli bir kadına rastlarsanız sakın cevap vermeyin. Kuchisake-onna efsanesine göre, 'Evet' derseniz maskesini çıkarır ve 'Peki ya şimdi?' diye sorar. Hayır derseniz... Sonuç hiç iyi olmaz.",
        "Evinizdeyken isminizin çağrıldığını duyarsanız ve evde yalnızsanız, sakın 'Efendim' demeyin veya o yöne gitmeyin. Bazı eski inanışlara göre bu, kötü niyetli varlıkların sizi kendi boyutlarına çekmek için kullandığı en eski tuzaktır."
    ],
    "BILGI": [
        "Eğer Dünya'daki tüm insanlar aynı anda okyanusa girseydi, su seviyesi sadece bir saç teli kalınlığı kadar yükselirdi. Okyanuslar o kadar büyüktür ki, biz insanlar onlar için bir hiçiz.",
        "Venüs gezegeninde bir gün, bir yıldan daha uzundur. Çünkü Venüs kendi etrafında o kadar yavaş döner ki, Güneş etrafındaki turunu tamamlaması daha kısa sürer."
    ],
    "MOTIVASYON": [
        "Bambu ağacı ilk 4 yıl hiç büyümez, sadece kök salar. Beşinci yıl ise 6 haftada 27 metre uzar. Senin emeğin de boşa gitmiyor, sadece kök salıyorsun. Sabret ve izle.",
        "Dünyanın en karanlık saati, güneş doğmadan hemen önceki saattir. Tam vazgeçmek üzere olduğun an, aslında zaferin sana en yakın olduğu andır. Devam et."
    ],
    "GIZEM": ["Bermuda Şeytan Üçgeni'nde kaybolan gemilerin çoğu asla bulunamadı. Ancak ilginç olan, bölgedeki manyetik alanın pusulaları sürekli kuzeyden saptırmasıdır. Bilim insanları bunun altındaki devasa metan gazı yataklarından kaynaklanabileceğini düşünüyor."],
    "GENEL": ["Ahtapotların üç kalbi vardır. Biri vücuda kan pompalar, diğer ikisi solungaçlara. Ayrıca kolları kopsa bile, o kollar bir süre daha hareket etmeye ve avlanmaya devam eder."]
}

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        sys.exit(1)
    return Credentials.from_authorized_user_info(json.loads(token_json))

# --- SES AYARLARI (DAHA DOĞAL) ---
async def generate_pro_voice(text, filename="voice.mp3"):
    # rate=+10% : Sesi %10 hızlandırır (Daha akıcı olur)
    # pitch=-2Hz : Sesi biraz kalınlaştırır (Daha tok olur)
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="+10%", pitch="-2Hz")
    await communicate.save(filename)

def create_video_pro(text, background_url, title_text):
    print(f"🎬 Video Başlıyor: {title_text}")
    
    # 1. Gelişmiş Ses Oluşturma
    asyncio.run(generate_pro_voice(text))
    audio = AudioFileClip("voice.mp3")
    print(f"🎙️ Ses Süresi: {audio.duration} sn")
    
    # 2. Video İndirme (Daha Güçlü User-Agent)
    print("📥 Video indiriliyor...")
    video_downloaded = False
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://www.pexels.com/'
    }
    
    try:
        r = requests.get(background_url, headers=headers, stream=True, timeout=40)
        if r.status_code == 200:
            with open("background.mp4", 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            if os.path.getsize("background.mp4") > 500000:
                video_downloaded = True
            else:
                print("⚠️ Video dosyası çok küçük!")
    except Exception as e:
        print(f"⚠️ İndirme Hatası: {e}")

    if not video_downloaded:
        print("🚨 Video inemedi, Siyah Ekran kullanılıyor.")
        background = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=audio.duration + 2)
    else:
        background = VideoFileClip("background.mp4")
        # Dikey Kırpma (Merkezden)
        if background.w > background.h:
            bg_ratio = background.w / background.h
            new_width = background.h * (9/16)
            background = background.crop(x_center=background.w/2, width=new_width, height=background.h)
        
        background = background.resize(height=1920)
        # Sadece orta kısmı al (Garanti 1080px)
        background = background.crop(x_center=background.w/2, width=1080, height=1920)
        background = background.fx(vfx.loop, duration=audio.duration + 2)

    # 3. Birleştirme
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    # Kırmızı Bantlı Başlık
    txt_clip = TextClip(title_text, fontsize=70, color='white', bg_color='#cc0000', 
                        size=(900, None), method='caption', align='center')
    txt_clip = txt_clip.set_pos(('center', 200)).set_duration(video.duration)
    
    final_video = CompositeVideoClip([video, txt_clip])
    final_video.write_videofile("shorts_video.mp4", fps=24, bitrate="5000k", codec="libx264", audio_codec="aac", preset='medium')
    return "shorts_video.mp4"

def upload_to_youtube(file_path, title, description, topic):
    try:
        creds = get_credentials()
        youtube = build('youtube', 'v3', credentials=creds)
        
        tags = ["shorts", "kesfet", topic.lower(), "ilgincbilgiler", "gizem"]
        
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "27"
                },
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(file_path)
        )
        response = request.execute()
        print(f"✅ YÜKLENDİ! Video ID: {response['id']}")
    except Exception as e:
        print(f"YouTube Hatası: {e}")
        sys.exit(1)

def main():
    day_name = datetime.now().strftime("%A")
    schedule = SCHEDULE.get(day_name, SCHEDULE["Sunday"])
    
    # Rastgele bir metin seç
    text = random.choice(CONTENT_POOL.get(schedule["topic"], CONTENT_POOL["GENEL"]))
    
    video_file = create_video_pro(text, schedule["video"], schedule["title"])
    
    title = f"{schedule['title']} | Bu Gerçek Mi? 😱 #shorts"
    description = f"{text[:80]}...\n\nAbone ol: @GolgeArsiviTR\n\n#shorts #{schedule['topic'].lower()}"
    
    upload_to_youtube(video_file, title, description, schedule["topic"])

if __name__ == "__main__":
    main()
