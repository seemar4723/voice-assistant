import os
import json
import pyttsx3
import wikipedia
import requests
import re
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from forex_python.converter import CurrencyRates
from serpapi import GoogleSearch
import time

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Initialize Google Translator
translator = Translator()

# API configuration
API_CONFIG = {
    'weather': 'b8963f3cdf1b88895c124f0236f7abed',
    'dictionary_api_url': 'https://api.dictionaryapi.dev/api/v2/entries/en/',
    'news_api_key': 'fcc923fe01d94e1c9e9eeeceb7dd8622',
    'serpapi_key': 'ee4682a750c6b4767e85cd7039a5bac6db326fdb353828af24778e1ae2e1a6e9'  # Your SerpAPI key
}

# To-Do list storage
todo_list = []

# Initialize currency converter
currency_rates = CurrencyRates()

def speak(text, lang='en'):
    """Convert text to speech, providing audio feedback to the user."""
    try:
        if lang == 'en':
            engine.say(text)
            engine.runAndWait()
        else:
            tts = gTTS(text=text, lang=lang)
            tts.save("temp.mp3")
            os.system("start temp.mp3")
            os.remove("temp.mp3")
        print(f"Assistant says: {text}")
    except Exception as e:
        print(f"An error occurred in speech synthesis: {e}")

def greet_user():
    """Greet the user at the start of the session."""
    speak("Hello, I'm your voice assistant. How can I help you?")

def take_voice_command():
    """Capture audio using the microphone and recognize the speech."""
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            print("Recognizing...")

            command = recognizer.recognize_google(audio, language='en-US')
            print(f"You said: {command}")
            return command.lower()

    except sr.UnknownValueError:
        print("Sorry, I did not catch that.")
        speak("Sorry, I did not catch that.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        speak("There was an issue with the recognition service.")
        return ""
    except sr.WaitTimeoutError:
        print("Listening timed out while waiting for phrase to start")
        speak("I didn't hear anything. Please try again.")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        speak("Something went wrong. Please try again.")
        return ""

def get_weather():
    """Ask for city and fetch weather information."""
    speak("Please tell me the city you want the weather for.")
    city = take_voice_command()
    if city:
        api_key = API_CONFIG['weather']
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(url)
        data = response.json()
       
        if data['cod'] == 200:
            weather = data['main']
            temperature = weather['temp'] - 273.15
            humidity = weather['humidity']
            description = data['weather'][0]['description']
            speak(f"The temperature in {city} is {temperature:.2f} degrees Celsius with {description}. Humidity is {humidity}%.")
        else:
            speak("Sorry, I couldn't fetch the weather information.")
    else:
        speak("I didn't catch the city name. Please try again.")

def define_word():
    """Ask for word and fetch the definition."""
    speak("Please tell me the word you want to define.")
    word = take_voice_command()
    if word:
        url = API_CONFIG['dictionary_api_url'] + word
        response = requests.get(url)
        data = response.json()

        if isinstance(data, list):
            meanings = data[0]['meanings'][0]['definitions'][0]['definition']
            speak(f"The definition of {word} is {meanings}.")
        else:
            speak(f"Sorry, I couldn't find the definition for {word}.")
    else:
        speak("I didn't catch the word. Please try again.")

def translate_text():
    """Ask for text and target language, then translate."""
    speak("Please tell me the text you want to translate.")
    text = take_voice_command()
    if text:
        speak("Please tell me the target language.")
        language = take_voice_command().lower()
        if language:
            translation = translator.translate(text, dest=language)
            speak(translation.text, lang=language)
        else:
            speak("I didn't catch the language. Please try again.")
    else:
        speak("I didn't catch the text. Please try again.")

def add_todo_item():
    """Ask for task and add it to the to-do list."""
    speak("Please tell me the task you want to add to your to-do list.")
    task = take_voice_command()
    if task:
        todo_list.append(task)
        speak(f"Added '{task}' to your to-do list.")
    else:
        speak("I didn't catch the task. Please try again.")

def show_todo_list():
    """Read out the to-do list."""
    if todo_list:
        items = ', '.join(todo_list)
        speak(f"Your to-do list includes: {items}.")
    else:
        speak("Your to-do list is empty.")

def send_email():
    """Ask for details and send an email."""
    speak("Please tell me the recipient's email address.")
    to_email = take_voice_command()
    if to_email:
        speak("Please tell me the subject of the email.")
        subject = take_voice_command()
        if subject:
            speak("Please tell me the body of the email.")
            body = take_voice_command()
            if body:
                sender_email = "your_email@gmail.com"
                sender_password = "your_password"

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    text = msg.as_string()
                    server.sendmail(sender_email, to_email, text)
                    server.quit()
                    speak("Email has been sent successfully.")
                except Exception as e:
                    speak(f"Failed to send email. Error: {e}")
            else:
                speak("I didn't catch the body of the email. Please try again.")
        else:
            speak("I didn't catch the subject. Please try again.")
    else:
        speak("I didn't catch the recipient's email. Please try again.")

def get_news():
    """Ask for category and fetch news."""
    predefined_categories = {
        'business': ['business', 'economy', 'finance', 'money', 'market'],
        'entertainment': ['entertainment', 'movies', 'film', 'music', 'celebrity'],
        'health': ['health', 'wellness', 'medical', 'medicine', 'fitness'],
        'science': ['science', 'space', 'research', 'technology'],
        'sports': ['sports', 'football', 'basketball', 'cricket', 'tennis', 'soccer'],
        'technology': ['technology', 'tech', 'gadgets', 'computers', 'innovation'],
        'general': ['general', 'news', 'headlines']
    }

    speak("Please tell me the news category you're interested in.")
    category_input = take_voice_command().lower()

    # Find the matching category based on keywords
    category = None
    for key, keywords in predefined_categories.items():
        for keyword in keywords:
            if keyword in category_input:
                category = key
                break
        if category:
            break

    if not category:
        speak("I didn't catch the category or it wasn't recognized. Fetching general news.")
        category = 'general'

    api_key = API_CONFIG['news_api_key']
    url = f"https://newsapi.org/v2/top-headlines?category={category}&apiKey={api_key}&country=us"
    response = requests.get(url)
    data = response.json()

    if data['status'] == 'ok':
        articles = data['articles'][:5]
        for article in articles:
            speak(article['title'])
    else:
        speak("Sorry, I couldn't fetch the news.")

def convert_currency():
    """Ask for amount and currencies, then convert."""
    speak("Please tell me the amount and the currency to convert from.")
    amount_input = take_voice_command()
   
    if amount_input:
        # Extract the numeric value
        amount_match = re.findall(r"[-+]?\d*\.\d+|\d+", amount_input)
       
        if not amount_match:
            speak("I couldn't detect a valid amount. Please try again.")
            return
       
        amount = float(amount_match[0])

        # Extract the currency from the command (assume the first currency mentioned is the 'from' currency)
        from_currency_match = re.findall(r'\b[A-Za-z]{3,}\b', amount_input)
        if from_currency_match:
            from_currency = from_currency_match[0].upper()
        else:
            speak("I couldn't detect the currency. Please try again.")
            return
       
        speak(f"Convert {amount} {from_currency} to which currency?")
        to_currency_input = take_voice_command()

        if to_currency_input:
            to_currency_match = re.findall(r'\b[A-Za-z]{3,}\b', to_currency_input)
            if to_currency_match:
                to_currency = to_currency_match[0].upper()
                try:
                    converted_amount = currency_rates.get_rate(from_currency, to_currency) * amount
                    speak(f"{amount} {from_currency} is {converted_amount:.2f} {to_currency}.")
                except Exception as e:
                    speak(f"Conversion failed. Error: {e}")
            else:
                speak("I couldn't detect the target currency. Please try again.")
        else:
            speak("I didn't catch the currency to convert to. Please try again.")
    else:
        speak("I didn't catch the amount or the currency. Please try again.")


def solve_math():
    """Ask for math problem and solve it."""
    speak("Please tell me the math problem you want to solve.")
    expression = take_voice_command()
    if expression:
        # Preprocess the expression
        expression = expression.lower()
        expression = expression.replace("what is", "").strip()
        expression = expression.replace("x", "*")  # Handle cases where 'x' is used for multiplication
        expression = expression.replace("times", "*")
        expression = expression.replace("plus", "+")
        expression = expression.replace("minus", "-")
        expression = expression.replace("divided by", "/")
        expression = expression.replace("over", "/")
       
        try:
            result = eval(expression)
            speak(f"The result of {expression} is {result}.")
        except Exception as e:
            speak(f"Sorry, I couldn't solve the math problem. Error: {e}")
    else:
        speak("I didn't catch the problem. Please try again.")

def start_quiz():
    """Ask for quiz question and search it on Google using SerpAPI."""
    speak("Please tell me your quiz question.")
    question = take_voice_command()

    if question:
        speak(f"Searching for the answer to: {question}.")
       
        params = {
            "engine": "google",
            "q": question,
            "api_key": API_CONFIG['serpapi_key'],
            "num": 1
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        # Try to find an answer in the answer box
        if 'answer_box' in results:
            answer = results['answer_box'].get('answer')
            if not answer:
                answer = results['answer_box'].get('snippet')
            if not answer:
                answer = results['answer_box'].get('title')

            if answer:
                speak(f"The answer is: {answer}")
            else:
                speak("Sorry, I couldn't find a specific answer.")
        elif 'organic_results' in results and results['organic_results']:
            top_result = results['organic_results'][0]
            answer = top_result.get('snippet', top_result.get('title', 'No answer found.'))
            speak(f"The top result says: {answer}")
        else:
            speak("Sorry, I couldn't find an answer to your question.")
    else:
        speak("I didn't catch the question. Please try again.")

def set_timer():
    """Ask for timer duration and set a timer."""
    speak("Please tell me the duration of the timer in minutes and/or seconds.")
    duration = take_voice_command()
    if duration:
        match = re.search(r'(\d+)\s*(minutes?|seconds?)', duration)
        if match:
            time_value = int(match.group(1))
            time_unit = match.group(2).lower()
            if 'minute' in time_unit:
                time_value *= 60
            speak(f"Setting a timer for {duration}.")
            time.sleep(time_value)
            speak("Time's up!")
        else:
            speak("I didn't catch the duration. Please try again.")
    else:
        speak("I didn't catch the duration. Please try again.")

def search_scholar():
    """Ask for topic and search for research papers on Google Scholar using SerpAPI."""
    speak("Please tell me the research topic.")
    topic = take_voice_command()
    if topic:
        speak(f"Searching for research papers on {topic}.")
        params = {
            "engine": "google_scholar",
            "q": topic,
            "api_key": API_CONFIG['serpapi_key']
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        for i, result in enumerate(results.get('organic_results', []), start=1):
            if i > 2:  # Limit to top 2 results for brevity
                break
            title = result.get('title', 'No title available')
            snippet = result.get('snippet', 'No snippet available')
            speak(f"Result {i}: {title}. Snippet: {snippet}")
            print(f"Title: {title}\nSnippet: {snippet}\n")
    else:
        speak("I didn't catch the topic. Please try again.")

def search_wikipedia():
    """Ask for topic and search Wikipedia."""
    speak("Please tell me the topic you want to search on Wikipedia.")
    topic = take_voice_command()
    if topic:
        speak(f"Searching Wikipedia for {topic}.")
        try:
            results = wikipedia.summary(topic, sentences=2)
            speak(f"According to Wikipedia: {results}")
        except wikipedia.DisambiguationError as e:
            speak(f"The topic is ambiguous. Here are some suggestions: {e.options[:5]}")
        except Exception as e:
            speak(f"An error occurred while searching Wikipedia: {e}")
    else:
        speak("I didn't catch the topic. Please try again.")

def recognize_command(command):
    """Recognize and process user commands."""
    command_mappings = {
        'weather': ['weather', 'temperature', 'forecast'],
        'define': ['define', 'meaning', 'what is'],
        'translate': ['translate', 'language'],
        'to-do': ['to-do', 'todo', 'tasks', 'notes'],
        'send email': ['send email', 'email', 'mail'],
        'news': ['news', 'headlines', 'current events'],
        'currency': ['currency', 'convert money', 'money exchange'],
        'solve': ['solve', 'calculate', 'math'],
        'quiz': ['quiz', 'ask me a question', 'quiz me'],
        'timer': ['timer', 'countdown', 'set a timer'],
        'wikipedia': ['wikipedia', 'wiki', 'encyclopedia'],
        'research': ['research', 'scholar', 'google scholar'],
        'exit': ['exit', 'goodbye', 'quit']
    }
   
    for key, keywords in command_mappings.items():
        if any(keyword in command for keyword in keywords):
            if key == 'weather':
                get_weather()
            elif key == 'define':
                define_word()
            elif key == 'translate':
                translate_text()
            elif key == 'to-do':
                if 'add' in command:
                    add_todo_item()
                elif 'show' in command or 'view' in command:
                    show_todo_list()
            elif key == 'send email':
                send_email()
            elif key == 'news':
                get_news()
            elif key == 'currency':
                convert_currency()
            elif key == 'solve':
                solve_math()
            elif key == 'quiz':
                start_quiz()
            elif key == 'timer':
                set_timer()
            elif key == 'wikipedia':
                search_wikipedia()
            elif key == 'research':
                search_scholar()
            elif key == 'exit':
                speak("Goodbye!")
                return False
    return True

def main():
    """Main function to run the assistant."""
    greet_user()
    while True:
        command = take_voice_command()
        if not recognize_command(command):
            break

if __name__ == "__main__":
    main()



