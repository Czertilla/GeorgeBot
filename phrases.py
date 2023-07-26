import  json
import logging
import re


logger = logging.getLogger(__name__)

def tell(code:str, lang:str='en', inset:dict={}, ignore_all_insets:bool=False) -> str:
    global data
    phrase: dict = data.get(code)
    if phrase == None:
        return 'unknown phrase code error'
    temp = phrase.get(lang, phrase.get('en'))
    if ignore_all_insets:
        temp = re.sub(r'<.*>', '', temp)
    for i, I in inset.items():
        temp = temp.replace(f'<{i}>', str(I), 1)
    return temp

with open('phrases.json', 'rb') as f:
    data: dict = json.load(f)
    language_codes = data["language_codes"].keys()
