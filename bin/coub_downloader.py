import os
import requests
import subprocess
import time
import sys

# --- НАСТРОЙКИ КАЧЕСТВА (можно менять) ---
VIDEO_QUALITY = "higher"   # higher, high, med
AUDIO_QUALITY = "high"     # high, med
# -----------------------------------------

# Заголовки, чтобы сервер думал, что запрос идет из браузера
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clear_screen():
    """Очищает экран консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Выводит красивый заголовок"""
    print("=" * 50)
    print("       COUB DOWNLOADER - с полной музыкой")
    print("=" * 50)
    print()

def get_coub_link():
    """Запрашивает ссылку у пользователя"""
    print("Введите ссылку на Coub:")
    print("Пример: https://coub.com/view/4aqg4q")
    print()
    link = input("👉 Ссылка: ").strip()
    
    # Если пользователь ввёл просто permalink (например, 4aqg4q)
    if not link.startswith("http"):
        if "/view/" in link:
            link = "https://coub.com/" + link
        else:
            link = f"https://coub.com/view/{link}"
    
    return link

def download_file(url, filename, file_type="файл"):
    """Скачивает файл с повторными попытками и индикатором прогресса"""
    for attempt in range(3):
        try:
            print(f"📥 Скачиваю {file_type}: {filename} (попытка {attempt+1}/3)")
            response = requests.get(url, stream=True, headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"   Прогресс: {percent:.1f}%", end='\r')
                
                print(f"\n   ✅ {file_type} скачан! ({downloaded / (1024*1024):.1f} MB)")
                return True
            else:
                print(f"   ❌ Ошибка HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            if attempt < 2:
                print("   ⏳ Повтор через 2 секунды...")
                time.sleep(2)
    
    print(f"   ❌ Не удалось скачать {file_type}")
    return False

def get_coub_data(permalink):
    """Получает данные о кубе через API Coub"""
    # Извлекаем permalink из полной ссылки
    if "coub.com/view/" in permalink:
        permalink = permalink.split("/view/")[1].split("?")[0]
    
    api_url = f"https://coub.com/api/v2/coubs/{permalink}"
    print(f"🔍 Запрашиваю данные: {api_url}")
    
    for attempt in range(3):
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            print("   ✅ Данные получены!")
            return response.json()
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Попытка {attempt+1}/3: Таймаут")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Попытка {attempt+1}/3: Ошибка соединения")
        except Exception as e:
            print(f"   ❌ Попытка {attempt+1}/3: {e}")
        
        if attempt < 2:
            print("   ⏳ Повтор через 2 секунды...")
            time.sleep(2)
    
    return None

def main():
    clear_screen()
    print_header()
    
    # Получаем ссылку от пользователя
    coub_url = get_coub_link()
    
    print()
    print(f"📌 Обрабатываю: {coub_url}")
    print()
    
    # 1. Получаем метаданные
    coub_data = get_coub_data(coub_url)
    if not coub_data:
        print("\n❌ Не удалось получить данные после нескольких попыток.")
        print("   Проверьте:")
        print("   • Интернет-соединение")
        print("   • Правильность ссылки")
        print("   • Доступность сайта coub.com")
        input("\nНажмите Enter для выхода...")
        return
    
    # Получаем название для файла
    title = coub_data.get('title', 'coub_video').replace(' ', '_')
    # Убираем недопустимые символы из названия
    title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    
    print(f"\n📝 Название: {title}")
    
    # Получаем длительность (для информации)
    duration = coub_data.get('duration', 0)
    print(f"⏱️  Длительность видео: {duration} сек")
    
    # 2. Находим ссылки на файлы
    video_versions = coub_data.get('file_versions', {}).get('html5', {}).get('video', {})
    audio_versions = coub_data.get('file_versions', {}).get('html5', {}).get('audio', {})
    
    # Выбираем видео
    if VIDEO_QUALITY in video_versions:
        video_url = video_versions[VIDEO_QUALITY]['url']
        print(f"🎬 Качество видео: {VIDEO_QUALITY}")
    elif 'high' in video_versions:
        video_url = video_versions['high']['url']
        print("🎬 Качество видео: high (higher недоступно)")
    else:
        video_url = list(video_versions.values())[0]['url']
        print("🎬 Качество видео: доступное по умолчанию")
    
    # Выбираем аудио
    if AUDIO_QUALITY in audio_versions:
        audio_url = audio_versions[AUDIO_QUALITY]['url']
        print(f"🎵 Качество аудио: {AUDIO_QUALITY}")
    else:
        audio_url = list(audio_versions.values())[0]['url']
        print("🎵 Качество аудио: доступное по умолчанию")
    
    print()
    
    # 3. Скачиваем файлы
    video_file = f"{title}_video.mp4"
    audio_file = f"{title}_audio.mp3"
    
    if not download_file(video_url, video_file, "видео"):
        print("\n❌ Скачивание видео не удалось")
        input("\nНажмите Enter для выхода...")
        return
    
    if not download_file(audio_url, audio_file, "аудио"):
        print("\n❌ Скачивание аудио не удалось")
        input("\nНажмите Enter для выхода...")
        return
    
    print("\n✅ Файлы скачаны. Объединяю...")
    
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
        # Запускаем ffmpeg с подавлением вывода (чтобы не захламлять консоль)
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("\n" + "=" * 50)
        print("🎉 ГОТОВО! 🎉")
        print("=" * 50)
        print(f"📁 Файл: {output_file}")
        
        size_mb = os.path.getsize(output_file) / (1024*1024)
        print(f"💾 Размер: {size_mb:.2f} MB")
        print(f"📂 Папка: {os.path.abspath('.')}")
        print("=" * 50)
        
        # Удаляем временные файлы (опционально)
        cleanup = input("\n🗑️  Удалить временные файлы (видео и аудио)? (y/n): ").lower()
        if cleanup == 'y' or cleanup == 'д':
            try:
                os.remove(video_file)
                os.remove(audio_file)
                print("✅ Временные файлы удалены")
            except:
                print("⚠️ Не удалось удалить некоторые файлы")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при объединении:")
        if e.stderr:
            print(e.stderr[-500:])  # Показываем последние 500 символов ошибки
        print("\nУбедитесь, что ffmpeg.exe находится в той же папке, что и скрипт")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    
    print()
    input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Прервано пользователем")
        input("\nНажмите Enter для выхода...")