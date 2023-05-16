import requests
import json

def get_gps_tles():
    url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle'
    response = requests.get(url)
    tle_data = response.text

    # Divide os TLEs em linhas
    tle_lines = tle_data.strip().split('\n')

    # Extrai as informações relevantes de cada TLE
    tles = []
    for i in range(0, len(tle_lines), 3):
        line1 = tle_lines[i].strip()
        line2 = tle_lines[i + 1].strip()

        if i + 2 < len(tle_lines):
            line3 = tle_lines[i + 2].strip()
        else:
            line3 = ''

        tle = {
            'line1': line1,
            'line2': line2,
            'line3': line3
        }

        tles.append(tle)

    return tles

def save_tles_to_json(tles, filename):
    with open(filename, 'w') as file:
        json.dump(tles, file, indent=4)

tles = get_gps_tles()
save_tles_to_json(tles, 'data/gps.json')
print(tles)