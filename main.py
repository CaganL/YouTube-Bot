import os
import random
import json
import asyncio
import edge_tts
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, vfx

# --- HİKAYE HAVUZU (Genişletildi ve Karışık) ---
STORIES = [
    {
        "topic": "KORKU",
        "title": "😱 GECE YARISI MİSAFİRİ",
        "text": "Japon efsanesi Kuchisake-onna'ya göre, gece sokakta maskeli bir kadın size 'Ben güzel miyim?' diye sorarsa sakın cevap vermeyin. Evet derseniz maskesini çıkarır ve 'Peki ya şimdi?' diye bağırır. Hayır derseniz... Sonuç hiç iyi olmaz."
    },
    {
        "topic": "BILGI",
        "title": "🪐 VENÜS'ÜN SIRRI",
        "text": "Venüs gezegeninde bir gün, bir yıldan daha uzundur. Çünkü Venüs kendi etrafında o kadar yavaş döner ki, Güneş etrafındaki turunu tamamlaması, kendi etrafındaki dönüşünden daha kısa sürer."
    },
    {
        "topic": "DENIZ",
        "title": "🌊 OKYANUSUN GÜCÜ",
        "text": "Eğer Dünya'daki tüm insanlar aynı anda okyanusa girseydi, su seviyesi sadece bir saç teli kalınlığı kadar yükselirdi. Okyanuslar o kadar devasa ve derindir ki, biz insanlar onun büyüklüğü yanında sadece bir hiçiz."
    },
    {
        "topic": "GIZEM",
        "title": "🚫 SAKIN CEVAP VERME",
        "text": "Evinizdeyken, boş bir odadan isminizin çağrıldığını duyarsanız sakın 'Efendim' demeyin veya o odaya gitmeyin. Bazı eski inanışlara göre bu ses, kötü niyetli varlıkların sizi kendi boyutlarına çekmek için kullandığı en eski tuzaktır."
    },
    {
        "topic": "ILGINC",
        "title": "🍌 MUZ VE İNSAN",
        "text": "İnsan DNA'sı ile muz DNA'sı %50 oranında benzerlik gösterir. Yani genetik olarak yarı yarıya bir muzla aynısınız. Bu, tüm canlıların ortak bir atadan geldiğinin en komik kanıtıdır."
    }
]

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    return Credentials.from_authorized_user_info(json.loads(token_json))

async def generate_pro_voice(text, filename="voice.mp3"):
    # Hızlı ve etkileyici anlatım
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural", rate="+10%", pitch="-2Hz")
    await communicate.save(filename)

def create_video_local(story_data):
    print(f"🎬 Video Başlıyor (LOCAL MOD): {story_data['title']}")
    
    # 1. Ses
    asyncio.run(generate_pro_voice(story_data['text']))
    audio = AudioFileClip("voice.mp3")
    
    # 2. Video (GitHub'a yüklediğin dosyayı kullanır)
    if not os.path.exists("background.mp4"):
        print("HATA: background.mp4 dosyası bulunamadı! Lütfen GitHub'a yükleyin.")
        sys.exit(1)
        
    background = VideoFileClip("background.mp4")
    
    # Dikey Kırpma ve Ayarlama
    if background.w > background.h:
        new_width = background.h * (9/16)
        background = background.crop(x_center=background.w/2, width=new_width, height=background.h)
    
    background = background.resize(height=1920)
    background = background.crop(x_center=background.w/2, width=1080, height=1920)
    
    # Loop (Döngü)
    background = background.fx(vfx.loop, duration=audio.duration + 2)
    
    # 3. Birleştirme
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    # Başlık
    txt_clip = TextClip(story_data['title'], fontsize=65, color='white', bg_color='#cc0000', 
                        size=(900, None), method='caption', align='center')
    txt_clip = txt_clip.set_pos(('center', 200)).set_duration(video.duration)
    
    final_video = CompositeVideoClip([video, txt_clip])
    final_video.write_videofile("shorts_video.mp4", fps=24, bitrate="6000k", codec="libx264", audio_codec="aac", preset='medium')
    return "shorts_video.mp4"

def upload_to_youtube(file_path, story_data):
    creds = get_credentials()
    youtube = build('youtube', 'v3', credentials=creds)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{story_data['title']} #shorts",
                "description": f"{story_data['text'][:80]}...\n\nAbone ol: @GolgeArsiviTR\n\n#shorts #kesfet #{story_data['topic'].lower()}",
                "tags": ["shorts", story_data['topic'].lower(), "gizem"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload(file_path)
    )
    response = request.execute()
    print(f"✅ YÜKLENDİ! Video ID: {response['id']}")

def main():
    # Rastgele hikaye seç
    story_data = random.choice(STORIES)
    video_file = create_video_local(story_data)
    upload_to_youtube(video_file, story_data)

if __name__ == "__main__":
    main()
