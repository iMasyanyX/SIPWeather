import time
from datetime import datetime
import requests
import pyttsx3
from pydub import AudioSegment
import paramiko
import os

# Словарь для локализации погодных условий
weather_conditions_ru = {
    'clear': 'ясно',
    'partly-cloudy': 'малооблачно',
    'cloudy': 'облачно с прояснениями',
    'overcast': 'пасмурно',
    'light-rain': 'небольшой дождь',
    'rain': 'дождь',
    'heavy-rain': 'сильный дождь',
    'showers': 'ливень',
    'wet-snow': 'дождь со снегом',
    'light-snow': 'небольшой снег',
    'snow': 'снег',
    'snow-showers': 'снегопад',
    'hail': 'град',
    'thunderstorm': 'гроза',
    'thunderstorm-with-rain': 'дождь с грозой',
    'thunderstorm-with-hail': 'гроза с градом'
}

def get_weather(api_key):
    url = 'https://api.weather.yandex.ru/v2/forecast'
    params = {'lat': 59.9342802, 'lon': 30.3350986, 'extra': 'true'}
    headers = {'X-Yandex-API-Key': api_key}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    try:
        fact = data['fact']
        condition = fact['condition']
        temperature = fact['temp']
        wind_speed = fact['wind_speed']

        forecasts = data['forecasts'][0]
        day_temperature = forecasts['parts']['day']['temp_avg']
        night_temperature = forecasts['parts']['night']['temp_avg']
        prec_prob = forecasts['parts']['day']['prec_prob']

        # Локализация погодного условия
        condition_ru = weather_conditions_ru.get(condition, condition)

        return condition_ru, temperature, wind_speed, prec_prob, day_temperature, night_temperature
    except KeyError:
        raise ValueError("Не удалось извлечь данные о погоде. Проверьте правильность API-ключа и структуру ответа.")

def text_to_speech(text, output_file):
    engine = pyttsx3.init(driverName='sapi5')  # Используйте SAPI5

    # Установка голоса RHVoice - Russian Elena по идентификатору
    engine.setProperty('voice', "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\TokenEnums\RHVoice\Irina")

    engine.save_to_file(text, output_file)
    engine.runAndWait()

def convert_to_wav(input_file, output_file, sample_width=2, channels=1, frame_rate=8000):
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_sample_width(sample_width)
    audio = audio.set_channels(channels)
    audio = audio.set_frame_rate(frame_rate)
    audio.export(output_file, format="wav")

def copy_to_remote_server(local_file, remote_folder, ssh_host, ssh_port, ssh_user, ssh_password):
    transport = paramiko.Transport((ssh_host, ssh_port))
    transport.connect(username=ssh_user, password=ssh_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_path = f"{remote_folder}/{local_file}"
    sftp.put(local_file, remote_path)

    sftp.close()
    transport.close()

def main():
    api_key = '123qwe'  # Замените на свой API-ключ

    ssh_host = '8.8.8.8'
    ssh_port = 22  # Порт SSH
    ssh_user = 'root'
    ssh_password = 'pwd'
    remote_folder = '/var/lib/asterisk/sounds/ru/custom/'

    while True:
        try:
            condition, temperature, wind_speed, prec_prob, day_temperature, night_temperature = get_weather(api_key)

            # Формирование текста для озвучивания
            text = f"Сегодня {condition.lower()}, температура сейчас - {temperature} градусов. Ветер - {wind_speed} метров в секунду. Температура днём - {day_temperature}, Температура ночью - {night_temperature}. Вероятность осадков - {prec_prob} процентов."
            print(text)

            # Озвучивание текста и сохранение в файл .wav
            tts_output_file = 'tts_output.wav'
            text_to_speech(text, tts_output_file)
            print("TTS OK")
            time.sleep(3)

            # Конвертация в нужный формат
            output_file = 'weather.wav'
            convert_to_wav(tts_output_file, output_file)
            print("TTS -> .wav OK")
            time.sleep(3)

            # Копирование на удаленный сервер
            copy_to_remote_server(output_file, remote_folder, ssh_host, ssh_port, ssh_user, ssh_password)
            print(".wav -> SSH OK")
            time.sleep(3)

        except Exception as e:
            print(f"Произошла ошибка: {e}")
        finally:
            # Удаление временных файлов
            if os.path.exists(tts_output_file):
                os.remove(tts_output_file)
            if os.path.exists(output_file):
                os.remove(output_file)
            print("OK,ожидаю 60 мин.")
            print("Текущее время:", datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
            print("=======================================")

        # Пауза на 60 минут перед следующей итерацией
        time.sleep(3600)

if __name__ == "__main__":
    main()