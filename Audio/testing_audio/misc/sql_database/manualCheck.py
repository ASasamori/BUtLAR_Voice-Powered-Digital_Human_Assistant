# pass in text
# 
# 
# # for correction

misspellings = {
    "foe": "PHO",
    "Foe": "PHO",
    "faux": "PHO",
    "Faux": "PHO",
    "kem": "CHEM",
    "cass": "CAS",
    "Cass": "CAS",
    "Chem": "CHEM",
    "chem": "CHEM",
    "Chemistry": "CHEM"
}

def obviousMispellings(text):
    print(f"Checking for obvious misspellings in: {text}")
    for word in misspellings:
        if word in text:
            print(f"Found misspelling: {word}")
            text = text.replace(word, misspellings[word])
    return text