import speech_recognition as sr
import pyttsx3
import datetime
import os
import pickle
import dateparser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Initialize the recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Function to speak text
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Google Calendar API Authentication
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def authenticate_google_calendar():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    
    return build("calendar", "v3", credentials=creds)

service = authenticate_google_calendar()

# Function to add a reminder to Google Calendar
def add_reminder(event_name, event_time):
    event = {
        "summary": event_name,
        "start": {"dateTime": event_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": (event_time + datetime.timedelta(hours=1)).isoformat(), "timeZone": "Asia/Kolkata"},
    }
    event = service.events().insert(calendarId="primary", body=event).execute()
    speak("Reminder added successfully!")

# Function to list upcoming reminders
def list_reminders():
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(calendarId="primary", timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime").execute()
    events = events_result.get("items", [])

    if not events:
        speak("No upcoming reminders.")
    else:
        speak("Here are your upcoming reminders:")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            speak(f"{event['summary']} at {start}")

# Function to listen for commands
def listen():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError:
            print("Could not request results.")
            return ""

# Main loop
while True:
    command = listen()

    if "hello" in command:
        speak("Hi, how can I assist you?")
    
    elif "set a reminder" in command:
        speak("What should I remind you about?")
        event_name = listen()

        speak("When should I remind you?")
        event_time_str = listen()
        event_time = dateparser.parse(event_time_str)

        if event_time:
            add_reminder(event_name, event_time)
        else:
            speak("I couldn't understand the time. Please try again.")
    
    elif "show my reminders" in command:
        list_reminders()

    elif "stop" in command:
        speak("Goodbye!")
        break

    else:
        speak("Sorry, I don't understand.")