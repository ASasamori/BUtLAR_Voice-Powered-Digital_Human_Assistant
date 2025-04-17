# pass in text
# 
# 
# # for correction
def obviousMispellings(text):
    if "foe" in text:
        text = text.replace("foe", "PHO")
    if "kem" in text:
        text = text.replace("kem", "CHEM")
    return text