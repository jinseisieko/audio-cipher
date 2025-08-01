import base64
import json
import os
import re
import time
from io import BytesIO

import requests
import soundfile as sf

from levenshtein_distance import levenshtein_distance

# sol1 - сервис участника, sol2 - сервис референсного решения
urls = ['http://127.0.0.1:8000/', 'http://127.0.0.1:8000/']

res = []
attempts_count = 0
while res != [200, 200]:
    res.clear()
    for url in urls:
        try:
            response = requests.get(url + '/ping', headers={'Content-Type': 'application/json'})
            res.append(response.status_code)
        except:
            pass
    attempts_count += 1
    time.sleep(0.5)
    if attempts_count > 30:
        print('cant ping :(')
        exit(1)

encoder_url = urls[0]
decoder_url = urls[1]

folder_path = 'tests'
pattern = re.compile(r'^test\d+\.txt$')
print("-"*40)

tests = sorted(f for f in os.listdir(folder_path) if pattern.match(f))
for file_name in tests:
    test_id = file_name.split('.')[0]

    # читаем текст теста
    text = open(os.path.join(folder_path, file_name), 'r', encoding='utf-8').read()

    # импортируем функцию-шума
    module = __import__(f'tests.{test_id}', fromlist=['f'])
    print(f'test: {test_id}', end=" ")

    if "description" in dir(module):
        print(f'\033[1;34m{module.description}\033[0m')
    distort = module.f

    try:
        # Encode
        resp = requests.post(
            encoder_url + '/encode',
            data=json.dumps({'text': text}),
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        resp.raise_for_status()
        wav_base64 = resp.json()['data']
        wav_bytes = base64.b64decode(wav_base64)

        # load wav to numpy
        audio, sr = sf.read(BytesIO(wav_bytes))

        # Проверка длительности
        duration_seconds = len(audio) / sr
        if duration_seconds > 10:
            raise ValueError(f'Audio duration exceeds 10 seconds: {duration_seconds:.2f}s')

        distorted_audio = distort(audio)

        # write back to wav bytes
        out_buf = BytesIO()
        sf.write(out_buf, distorted_audio, sr, format='WAV', subtype='PCM_16')
        out_buf.seek(0)
        new_base64 = base64.b64encode(out_buf.read()).decode('utf-8')

        # Decode
        resp = requests.post(
            decoder_url + '/decode',
            data=json.dumps({'data': new_base64}),
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        resp.raise_for_status()
        decoded_text = resp.json()['text']
        ld = levenshtein_distance(text, decoded_text)
        if ld/len(text) < 0.1:
            print(f'\033[31mdif\033[0m: \033[32m{levenshtein_distance(text, decoded_text)} ({int(ld/len(text)*100)}%)\033[0m')
        else:
            print(f'\033[31mdif\033[0m: {levenshtein_distance(text, decoded_text)} ({int(ld/len(text)*100)}%)')
    except Exception as e:
        print(f'\033[31merror: {e}\033[0m')
        print('\033[31mdif\033[0m: 1e9 (>100%)')
    print("-"*40)
