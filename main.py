import speech_recognition as sr
import pyttsx3
import datetime
import os
import pickle
import dateparser
import smtplib
import pywhatkit
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import emaildetails

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

# Function to get input from voice or keyboard
def get_input(prompt):
    speak(prompt)
    choice = input("Press 'V' for voice input or 'K' for keyboard input: ").strip().lower()
    if choice == 'v':
        return listen()
    elif choice == 'k':
        return input("Type your response: ").strip()
    else:
        speak("Invalid choice. Defaulting to keyboard input.")
        return input("Type your response: ").strip()

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

# Function to send an email
def send_email(to_email, subject, message):
    sender_email = emaildetails.Name
    sender_password = emaildetails.Password
    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    
    msg.attach(MIMEText(message, "plain"))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        speak("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
        speak("Failed to send email.")

def send_whatsapp_message(phone_number, message):
    try:
        hour = datetime.datetime.now().hour
        minute = datetime.datetime.now().minute + 2  # Send message after 2 minutes
        pywhatkit.sendwhatmsg(phone_number, message, hour, minute)
        speak("WhatsApp message sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
        speak("Failed to send WhatsApp message.")

# Main loop
while True:
    command = get_input("How can I assist you?")

    if "hello" in command:
        speak("Hi, how can I assist you?")
    
    elif "set reminder" in command:
        event_name = get_input("What should I remind you about?")
        event_time_str = get_input("When should I remind you?")
        event_time = dateparser.parse(event_time_str)

        if event_time:
            add_reminder(event_name, event_time)
        else:
            speak("I couldn't understand the time. Please try again.")
    
    elif "show reminders" in command:
        list_reminders()
    
    elif "send email" in command:
        recipient = get_input("To whom should I send the email?")
        subject = get_input("What is the subject of the email?")
        message = get_input("What should I say in the email?")
        send_email(recipient, subject, message)
    
    elif "send message" in command:
        phone_number = get_input("To which phone number should I send the message?")
        message = get_input("What message should I send?")
        send_whatsapp_message(phone_number, message)

    elif "stop" in command:
        speak("Goodbye!")
        break
    
    else:
        speak("Sorry, I don't understand.")
