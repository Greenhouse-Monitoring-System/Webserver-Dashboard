import os
from twilio.rest import Client
import toml
import pywhatkit

with open('config.toml', 'r') as f:
    config = toml.load(f)

account_sid = config["twilio"]["TWILIO_ACCOUNT_SID"]
auth_token = config["twilio"]["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


def send_message(text):
    message = client.messages.create(
    body=text,
    from_="whatsapp:+14155238886",
    to='whatsapp:'+config["twilio"]["phone_number"]
)

send_message("Hello There Welcome to GreenHouse Meta\nTemp: 30C, Hum: 60%\nPlease Keep track of your greenhouse")
