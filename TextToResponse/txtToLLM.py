import manualCheck
#import pandas as pd


# import transcript
with open("../SpeechToText/transcript.txt", "r") as file:
    text = file.read()

#manual check
text = manualCheck.obviousMispellings(text)
print(text)

#feed to LLM now
#still not sure how id feed this with a whole sentence
professorsNames = {}

# Option 1: Prompt engineer
# Option 2: lightweight + fast: fuzzy matching
