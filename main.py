import os
import random
import json
import requests
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, vfx

# --- UZUN HİKAYELER LİSTESİ (Her biri yaklaşık 30-40 sn sürer) ---
STORIES = [
    "1990 yılında Japonya'da bir adam, evindeki yiyeceklerin sürekli kaybolduğundan şüphelenmeye başladı. Başta hafızasını kaybettiğini düşündü. Ancak bir gün mutfağa gizli kamera yerleştirdi. Görüntüleri izlediğinde kanı dondu. Evde kimse yokken, mutfak dolabının en üst rafından yaşlı bir kadın çıkıyor, yiyecekleri yiyor ve tekrar dolaba girip saklanıyordu. Kadının adamın evinde, o dolabın içinde tam bir yıldır yaşadığı ortaya çıktı.",
    
    "Rus uyku deneyi efsanesine göre, 1940'larda 5 savaş esiri, özel bir gaz verilerek 15 gün boyunca uyanık tutuldu. İlk 5 gün her şey normaldi ama sonra denekler çığlık atmaya ve kendilerine zarar vermeye başladı. 15. günün sonunda gaz kesilip odaya girildiğinde, deneklerden biri korkunç bir haldeydi. Doktorlar onu kurtarmaya çalışırken, o sadece gülümseyip şöyle fısıldadı: Biz sizin yatağın altındaki canavarlarız. Biz sizin zihninizin derinliklerinde saklanan deliliğiz.",
    
    "Titanic batmadan 14 yıl önce, Morgan Robertson adında bir yazar 'Titan' adında devasa bir gemiyi anlatan bir roman yazdı. Kitaptaki gemi de batmaz deniyordu, o da bir buzdağına çarptı ve o da Nisan ayında, Kuzey Atlantik'te battı. Kitaptaki geminin yolcu sayısı ve filika eksikliği bile gerçek Titanic ile neredeyse birebir aynıydı. Bu bir tesadüf mü, yoksa korkutucu bir kehanet mi?",
    
    "Paris'teki yer altı mezarları, altı milyondan fazla insanın kemikleriyle doludur. Ancak bu tünellerin sadece küçük bir kısmı haritalanmıştır. 1990'larda bulunan bir el kamerası kaydında, bir adamın tünellerde kaybolduğu ve panik içinde koştuğu görülür. Videonun sonunda adam kamerayı düşürür ve karanlığın içine doğru koşar. O adamdan bir daha asla haber alınamadı ve kameranın bulunduğu yer, haritalanmamış yasak bölgenin derinliklerindeydi."
]

def get_credentials():
    token_json = os.environ.get("TOKEN_JSON")
    if not token_json:
        print("HATA: TOKEN_JSON bulunamadı!")
        sys.exit(1)
    creds_data = json.loads(token_json)
    return Credentials.from_authorized_user_info(creds_data)

def download_background():
    # Arkaya gerilim müziğine uygun, gizemli bir orman/yol videosu
    url = "https://videos.pexels.com/video-files/3690666/3690666-hd_1080_1920_25fps.mp4"
    
    print("Arka plan videosu indiriliyor...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, stream=True, timeout=20)
        r.raise_for_status()
        with open("background.mp4", 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("İndirme başarılı!")
        return True
    except Exception as e:
        print(f"Video indirilemedi: {e}")
        return False

def create_video(text):
    print(f"Video hazırlanıyor (Uzun Versiyon): {text[:30]}...")
    
    # 1. Sesi Oluştur (Uzun metin)
    tts = gTTS(text, lang='tr', slow=False)
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    print(f"Ses süresi: {audio.duration} saniye")
    
    # 2. Arka Planı Hazırla
    download_success = download_background()
    
    if download_success and os.path.exists("background.mp4"):
        background = VideoFileClip("background.mp4")
        
        # --- ÖNEMLİ: VİDEOYU UZATMA (LOOP) ---
        # Eğer ses 40 saniye ama video 10 saniyeyse, video 4 kere dönmeli.
        if background.duration < audio.duration + 2:
            print("Video sesten kısa, döngüye (loop) alınıyor...")
            # Videoyu ses süresi kadar uzat (loop)
            background = background.fx(vfx.loop, duration=audio.duration + 2)
            
        # Dikey değilse kırp (Garanti olsun)
        if background.w > background.h:
             background = background.crop(x1=background.w/2 - 270, width=540, height=960) # Basit crop
             
    else:
        # Video inmezse Siyah Ekran
        background = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=audio.duration + 2)
    
    # 3. Videoyu Sese Eşitle
    video = background.set_duration(audio.duration + 1.5)
    video = video.set_audio(audio)
    
    # 4. Yazıyı Ekle (Daha okunaklı olması için)
    # Metni çok uzun olduğu için ekrana sığdırmak zor olabilir, 
    # şimdilik basit bir başlık atıyoruz, metin sesli okunacak.
    
    title_text = "SONUNA KADAR DİNLE! 😱"
    txt_clip = TextClip(title_text, fontsize=60, color='white', bg_color='red', 
                        size=(800, None), method='caption')
    txt_clip = txt_clip.set_pos(('center', 200)).set_duration(video.duration)
    
    # 5. Birleştir
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
                    "tags": ["shorts", "korku", "hikaye", "gizem"],
                    "categoryId": "27" # Eğitim/Bilgi kategorisi
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
        story = random.choice(STORIES)
        video_file = create_video(story)
        
        # Başlığı kısaltıp ilgi çekici yapalım
        title = "Bunu Duyunca Uyuyamayacaksın! 😱 #shorts"
        description = f"İlginç bir hikaye: {story[:50]}...\n\n#shorts #korku #gizem #hikaye"
        
        upload_to_youtube(video_file, title, description)
    except Exception as e:
        print(f"Genel Hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
