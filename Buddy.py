import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import json

# Load Gemini API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ========== MEMORY SYSTEM ==========
MEMORY_FILE = "jarvis_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"name": None, "preferences": {}, "last_topic": None, "chat_history": []}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

memory = load_memory()

# ========== VOICE FUNCTIONS ==========
def speak(text):
    engine = pyttsx3.init('sapi5')  # 'nsss' for Mac, 'espeak' for Linux
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Jarvis: I'm listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except:
        return None

# ========== COMMAND HANDLER ==========
def handle_command(command):
    command = command.lower()

    # Time
    if "time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")
        memory["last_topic"] = "time"
        save_memory()
        return True

    # Open YouTube
    elif "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")
        memory["last_topic"] = "youtube"
        save_memory()
        return True

    # Google search
    elif "search google for" in command:
        query = command.replace("search google for", "").strip()
        if query:
            speak(f"Searching Google for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            memory["last_topic"] = query
            save_memory()
        else:
            speak("What should I search for?")
        return True

    # Save user name
    elif "my name is" in command:
        name = command.replace("my name is", "").strip().capitalize()
        memory["name"] = name
        save_memory()
        speak(f"Nice to meet you, {name}!")
        return True

    # Save preference
    elif "i like" in command:
        pref = command.replace("i like", "").strip()
        memory["preferences"][pref] = True
        save_memory()
        speak(f"Got it, you like {pref}. I'll remember that.")
        return True

    return False

# ========== MAIN ==========
if memory["name"]:
    speak(f"Welcome back, {memory['name']}! How can I help you today?")
else:
    speak("Hello, I am Jarvis. What is your name?")

time.sleep(0.5)

while True:
    command = listen()
    if command:
        print(f"You said: {command}")

        # Exit condition
        if "stop" in command or "exit" in command or "quit" in command:
            speak("Goodbye! I'll remember our conversation for next time.")
            save_memory()
            break

        # Check if it's a real-world command
        handled = handle_command(command)

        if not handled:
            # ========== CHAT HISTORY MODE ==========
            try:
                # Add user message to history
                memory["chat_history"].append({"role": "user", "content": command})

                # Keep only last 10 exchanges to save token cost
                recent_history = memory["chat_history"][-10:]

                # Format context for Gemini
                context = "This is a conversation between the user and Jarvis. Keep responses short and natural.\n"
                if memory["name"]:
                    context += f"The user's name is {memory['name']}.\n"
                if memory["preferences"]:
                    context += f"User preferences: {list(memory['preferences'].keys())}\n"

                for msg in recent_history:
                    context += f"{msg['role'].capitalize()}: {msg['content']}\n"

                # Ask Gemini
                response = model.generate_content(context)
                reply = response.text.strip()

                # Add reply to history
                memory["chat_history"].append({"role": "jarvis", "content": reply})
                memory["last_topic"] = command
                save_memory()

                # Speak reply
                print(f"Jarvis: {reply}")
                speak(reply)

            except Exception as e:
                print("Gemini error:", e)
                speak("Sorry, I had trouble connecting to my brain.")
    else:
        speak("Sorry, I didn't catch that.")
