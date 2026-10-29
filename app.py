from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__)

def extract_video_id(url)
    match = re.search(r'(v=)([0-9A-Za-z_-]{11}).', url)
    return match.group(1) if match else None

@app.route('transcript', methods=['GET'])
def get_transcript()
    url = request.args.get('url')
    if not url
        return jsonify({'error' 'URL parametresi gerekli'}), 400
    
    video_id = extract_video_id(url)
    if not video_id
        return jsonify({'error' 'Geçersiz YouTube Linki'}), 400

    try
        # YouTube'dan Türkçe altyazıyı çekmeyi deneyelim, yoksa ilk dili alalım
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        
        try
            transcript = transcript_list.find_transcript(['tr'])
        except
            for tr in transcript_list
                transcript = tr
                break
                
        if not transcript
            return jsonify({'error' 'Altyazı bulunamadı'}), 404

        data = transcript.fetch()
        full_text =  .join([item['text'] for item in data])
        
        return jsonify({'success' True, 'transcript' full_text})
        
    except Exception as e
        return jsonify({'error' str(e)}), 500

if __name__ == '__main__'
    app.run(host='0.0.0.0', port=5000)