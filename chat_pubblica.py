
import openai
import streamlit as st
from better_profanity import profanity
from profanity_check import predict

# Directly setting the API keys (for example, replace with your real keys)
openai.api_key = "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"
SUPABASE_URL = "https://ljrjaehrttxhqejcueqj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqcmphZWhydHR4aHFlamN1ZXFqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxODU4OTcsImV4cCI6MjA1ODc2MTg5N30.wfbzum88wn0b0OVw6WlMunOWvLvnfIjqnRyGeEQLghY"
OPENWEATHER_API_KEY = "d23fb9868855e4bcb4dcf04404d14a78"

# Extended blacklist for offensive words in Italian
blacklist_words_it = [
    "stronzo", "cazzo", "merda", "schifo", "idiota", "cretino", "violenza", "terrorismo", 
    "morte", "omicidio", "puttana", "bastardo", "vaffanculo", "porco", "stupido", "testa di cazzo"
]

# Function to check for offensive words using profanity library
def check_profanity(text):
    # Check if the text contains any blacklisted words
    for word in blacklist_words_it:
        if word in text.lower():
            st.write(f"Profanity detected: {word}")  # Debug log for profanity
            return True
    if profanity.contains_profanity(text):
        st.write(f"Profanity detected using better_profanity")  # Debug log for profanity
        return True
    return False

# Function to check the content using OpenAI API for harmful intent
def check_with_openai(text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003", 
            prompt=f"Analyze the following text and determine if it contains any harmful or abusive language: {text}",
            max_tokens=60
        )
        st.write(f"OpenAI response: {response.choices[0].text}")  # Debug log for OpenAI response
        if 'abusive' in response.choices[0].text.lower():
            return True
    except Exception as e:
        st.error(f"Error with OpenAI API: {e}")
    return False

# Main filter function to handle incoming messages
def filter_message(message):
    st.write(f"Filtering message: {message}")  # Debug log for message being filtered
    if check_profanity(message):
        return "Questo messaggio è stato censurato per contenuti inappropriati."
    elif check_with_openai(message):
        return "Questo messaggio è stato censurato per contenuti dannosi o offensivi."
    else:
        return message
