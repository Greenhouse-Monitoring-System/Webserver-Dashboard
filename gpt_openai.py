from openai import OpenAI
import tomllib

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

API_KEY= config["API"]["GPTAPI"]

client = OpenAI(api_key=API_KEY)

def askGPT(question):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {"role": "developer", "content": "You are a helpful gardening assistant that guides the user through a greenhouse"
                                             "journey where they can plant whatever plants and you help them through instructions"
                                             "and planting and tell them ideal environment for that plant."
                                             "Return the answer in HTML format (just the card part without the headers and html tag"
                                             " and have the width of the card set to 100%) using the Bootstrap card layout."},
            {"role": "user", "content": question}
        ]
    )
    return completion.choices[0].message.content