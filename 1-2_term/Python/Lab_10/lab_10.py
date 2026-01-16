#1 вариант
import requests
import pyttsx3
import webbrowser
from vosk import Model, KaldiRecognizer
import pyaudio

DOGS_SAVED_COUNT = 0

def get_dog_image():
    response = requests.get("https://dog.ceo/api/breeds/image/random")
    if response.status_code == 200:
        data = response.json()
        return data['message']
    else:
        return None

def save_image(url, filename="dog_image.jpg"):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        return True
    else:
        return False

def speak(say):
    engine.say(say)
    engine.runAndWait()

def recognize_speech():
    print("Говорите")

    while True:
        data = stream.read(4096)
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            return result

def main():
    dog_image_url = get_dog_image()
    global DOGS_SAVED_COUNT
    speak("Привет!")
    while True:
        command = recognize_speech().lower()

        if "показать" in command:
            if dog_image_url:
                webbrowser.open(dog_image_url)
            else:
                speak("Не удалось получить доступ к изображению собаки.")

        elif "сохранить" in command:
            if dog_image_url:
                DOGS_SAVED_COUNT += 1
                if save_image(dog_image_url, filename=f"Dog_{DOGS_SAVED_COUNT}.jpg"):
                    speak("Изображение сохранено.")
                else:
                    DOGS_SAVED_COUNT -= 1
                    speak("Не удалось сохранить изображение.")
            else:
                speak("Не удалось получить доступ к изображению собаки.")

        elif "следующая" in command:
            dog_image_url = get_dog_image()
            if dog_image_url:
                speak("Изображение обновлено.")
                webbrowser.open(dog_image_url)
            else:
                speak("Не удалось получить доступ к изображению собаки.")

        elif "назвать породу" in command:
            if dog_image_url:
                breed = dog_image_url.split('/')[-2]
                speak(f"Порода собаки: {breed}.")
            else:
                speak("Не удалось получить доступ к изображению собаки.")

        elif "выход" in command:
            speak("До свидания!")
            break
        
        else:
            print("Команда не распознана")

     
engine = pyttsx3.init()
engine.setProperty('rate', 120)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[87].id)
model = Model("Lab_10/model/vosk-model-small-ru-0.4")
recognizer = KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

main()    
stream.stop_stream()
stream.close()
p.terminate()
