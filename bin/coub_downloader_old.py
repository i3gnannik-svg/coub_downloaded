import os
import requests
import subprocess
import time

# --- НАСТРОЙКИ ---
COUB_URL = "https://coub.com/view/4aqg4q"
VIDEO_QUALITY = "higher"   # higher, high, med
AUDIO_QUALITY = "high"     # high, med
# -----------------

# Заголовки, чтобы сервер думал, что запрос идет из браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def download_file(url, filename):
    """Скачивает файл с повторными попытками"""
    for attempt in range(3):
        try:
            print(f"Скачиваю: {filename} (попытка {attempt+1})")
            response = requests.get(url, stream=True, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            else:
                print(f"Ошибка HTTP {response.status_code}")
        except Exception as e:
            print(f"Ошибка: {e}")
            if attempt < 2:
                print("Повтор через 2 секунды...")
                time.sleep(2)
    return False

def get_coub_data(permalink):
    """Получает данные о кубе через API Coub"""
    # Извлекаем permalink из полной ссылки
    if "coub.com/view/" in permalink:
        permalink = permalink.split("/view/")[1].split("?")[0]
    
    api_url = f"https://coub.com/api/v2/coubs/{permalink}"
    print(f"Запрашиваю данные с API: {api_url}")
    
    for attempt in range(3):
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Попытка {attempt+1} не удалась: {e}")
            if attempt < 2:
                print("Повтор через 2 секунды...")
                time.sleep(2)
    return None

def main():
    print("=== Coub Downloader (с полным аудио) ===")
    
    # 1. Получаем метаданные
    coub_data = get_coub_data(COUB_URL)
    if not coub_data:
        print("Не удалось получить данные после нескольких попыток.")
        print("Проверьте интернет и доступность сайта coub.com")
        return
    
    # Получаем название для файла
    title = coub_data.get('title', 'coub_video').replace(' ', '_')
    title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    print(f"Название: {title}")
    
    # 2. Находим ссылки на файлы
    video_versions = coub_data.get('file_versions', {}).get('html5', {}).get('video', {})
    audio_versions = coub_data.get('file_versions', {}).get('html5', {}).get('audio', {})
    
    # Выбираем видео
    if VIDEO_QUALITY in video_versions:
        video_url = video_versions[VIDEO_QUALITY]['url']
    elif 'high' in video_versions:
        video_url = video_versions['high']['url']
    else:
        video_url = list(video_versions.values())[0]['url']
    
    # Выбираем аудио
    if AUDIO_QUALITY in audio_versions:
        audio_url = audio_versions[AUDIO_QUALITY]['url']
    else:
        audio_url = list(audio_versions.values())[0]['url']
    
    print(f"Видео: {video_url}")
    print(f"Аудио: {audio_url}")
    
    # 3. Скачиваем файлы
    video_file = f"{title}_video.mp4"
    audio_file = f"{title}_audio.mp3"
    
    if not download_file(video_url, video_file):
        print("Не удалось скачать видео")
        return
    if not download_file(audio_url, audio_file):
        print("Не удалось скачать аудио")
        return
    
    print("Файлы скачаны. Объединяю...")
    
    # 4. Объединяем с зацикливанием видео
    output_file = f"{title}_merged.mp4"
    cmd = [
        'ffmpeg',
        '-stream_loop', '-1',
        '-i', video_file,
        '-i', audio_file,
        '-shortest',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-y',
        output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"ГОТОВО! Файл сохранен: {output_file}")
        size_mb = os.path.getsize(output_file) / (1024*1024)
        print(f"Размер файла: {size_mb:.2f} MB")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка FFmpeg: {e.stderr}")
        print("Убедитесь, что ffmpeg.exe находится в той же папке, что и скрипт")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()