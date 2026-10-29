from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import whisper
import os
import re

app = Flask(__name__)

# Whisper modelini yüklüyoruz (Sunucuyu yormamak için en hızlı ve hafif model olan 'tiny' kullanıyoruz)
model = whisper.load_model("tiny")

def extract_video_id(url):
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return match.group(1) if match else None

def transcribe_with_whisper(url):
    audio_filename = "temp_audio.mp3"
    try:
        # yt-dlp ile YouTube videosunun sadece sesini indiriyoruz
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_audio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Whisper ile sesi metne döküyoruz
        result = model.transcribe("temp_audio.mp3")
        
        # Geçici ses dosyasını sunucudan siliyoruz
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
            
        return result["text"]
    except Exception as e:
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        raise e

@app.route('/transcript', methods=['GET'])
def get_transcript():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parametresi gerekli'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Geçersiz YouTube Linki'}), 400

    try:
        # 1. Önce YouTube'un kendi altyazısını deniyoruz (Hızlı yöntem)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        
        try:
            transcript = transcript_list.find_transcript(['tr'])
        except:
            for tr in transcript_list:
                transcript = tr
                break
                
        if transcript:
            data = transcript.fetch()
            full_text = " ".join([item['text'] for item in data])
            return jsonify({'success': True, 'transcript': full_text, 'method': 'youtube_transcript'})
            
    except Exception:
        pass # Altyazı bulunamadıysa Whisper'a geçilecek

    # 2. Altyazı yoksa Whisper yapay zekası ile sesten metne çeviriyoruz (Yavaş ama kesin çözüm)
    try:
        whisper_text = transcribe_with_whisper(url)
        return jsonify({'success': True, 'transcript': whisper_text, 'method': 'whisper_ai'})
    except Exception as e:
        return jsonify({'error': f'Altyazı bulunamadı ve Yapay Zeka ses analizi başarısız oldu: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)