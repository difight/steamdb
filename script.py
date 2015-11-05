
import steam
import steamdb
import msgpack
import time
from pprint import pprint
from datetime import date, datetime


def mark_and_update():

    # steamdb.queue_app_update()

    while steamdb.update_next_app():
        time.sleep(3)
    


def update_all():
    for app_id in steam.get_steam_apps_by_id().keys():
        steamdb.get_raw_app_details(app_id)
        print(app_id)
        time.sleep(5)


def refresh_list():
    steamdb.update_app_list()


def count_keys(type=None):

    ct = 0
    d = {}

    for app_id, app_info, update_time in steamdb.load_all_raw_app_details():
        if type is not None and app_info.get(b'type') != type:
            continue
        ct += 1
        for k in app_info.keys():
            d[k] = 1 + d.get(k, 0)

    print(ct)
    pprint(list(reversed(sorted([(v / ct, k) for k, v in d.items()]))))

    
def count_values(key, number=None, type=None):

    if number is None:
        number = 9999999
    
    d = {}
    ct = 0

    for app_id, app_info, update_time in steamdb.load_all_raw_app_details():
        if type is not None and app_info.get(b'type') != type:
            continue
        ct += 1
        vkey = str(app_info.get(key))
        d[vkey] = 1 + d.get(vkey, 0)

    print(ct)
    pprint(
        list(
            reversed(
                sorted([(v, k) for k, v in d.items()])
            )
        )[:number]
    )


def show(id):
    
    pprint(steamdb.load_raw_app_details(id))



def parse_dates():
    """Parse all release dates into actual dates."""

    formats = (
        '%d %b %Y', '%d %b, %Y',
        '%b %Y',
    )
    def parse_d(val, i=0):
        if i >= len(formats):
            return None
        try:
            return datetime.strptime(val, formats[i]).date()
        except ValueError:
            return parse_d(val, i + 1)

    for app_id, app_info, update_time in steamdb.load_all_raw_app_details():
        val = app_info[b'release_date'][b'date'].decode('ascii')
        release_date = parse_d(val)
        #if release_date is not None and release_date > date.today():
        #    release_date = None

        if release_date is None and val != '':
            print(release_date, repr(val), app_id)


def read_genres(number=None):
    """Find the IDs of the available genres."""

    if number is None:
        number = 9999999
    
    d = {}
    ct = 0

    for app_id, app_info, update_time in steamdb.load_all_raw_app_details():
        ct += 1
        genres = app_info.get(b'genres', [])
        for genre in genres:
            vkey = genre.get(b'id')
            vval = genre.get(b'description')
            countdict = d.get(vkey, {})
            countdict[vval] = 1 + countdict.get(vval, 0)
            d[vkey] = countdict

    print(ct)
    pprint(d)


def read_categories():
    """Find the IDs of the available categories."""
    d = {}
    ct = 0

    for app_id, app_info, update_time in steamdb.load_all_raw_app_details():
        ct += 1
        categories = app_info.get(b'categories', [])
        for category in categories:
            vkey = category.get(b'id')
            vval = category.get(b'description')
            countdict = d.get(vkey, {})
            countdict[vval] = 1 + countdict.get(vval, 0)
            d[vkey] = countdict

    print(ct)
    categories = {}
    for ct_id in d:
        name = max((v,k) for k,v in d[ct_id].items())[1]
        print(name)
        categories[ct_id] = name.decode('ascii')

    pprint(categories)


STRUCTURE = {
    #'type': ['game', 'dlc', 'movie', 'demo', 'advertising', 'video', 'mod', 'hardware'],
    #'website': str,

    'screenshots': [{'id': 123, 'path_full': 'url', 'path_thumbnail': 'url'}],

    'support_info': {'url': str, 'email': str},
    #'required_age': str,

    #'release_date': {'coming_soon': False, 'date': '1 Jan[,] 2000 oder 11/07/15 oder "Shootin for 2017'},

    # 'publishers': str,
    #'platforms': {'windows': True, 'mac': True, 'linux': False},

    #'name': str,
    #'pc_requirements': 'html',
    #'mac_requirements': 'html',
    #'linux_requirements': 'html',

    #'is_free': True,
    # 'header_image': 'image url',
    #'detailed_description': 'html',
    #'background': 'image url (unusable)',
    #'about_the_game': 'html',

# optionals
    #'supported_languages': str,
    #'developers': ['name', ],
    #'categories': [{'id': 2, 'description': b'Single-player'}, ],
    #'genres': [{'id': '1', 'description': 'something'}, ],
    #'packages': 'ignore',
    'price_overview': {'initial': 123, 'discount_percent': 0, 'final': 123, 'currency': 'EUR'},
    'movies': [{
        'highlight': False,
        'webm': {
            'max': 'http://cdn.akamai.steamstatic.com/steam/apps/2030748/movie_max.webm?t=1391610517',
            '480': b'http://cdn.akamai.steamstatic.com/steam/apps/2030748/movie480.webm?t=1391610517'},
        'id': 2030748,
        'thumbnail': 'http://cdn.akamai.steamstatic.com/steam/apps/2030748/movie.293x165.jpg?t=1391610517',
        'name': b'realMyst: ME Times'}, ],
    'achievements': {'total': 1, 'highlighted':
                     [
                         {'name': '0% Achievement Padawan',
                       'path': 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/apps/225600/8ba2c87a33813528300b3d73467ea0213039a642.jpg'
                      }
                     ]
                 },
    'legal_notice': str,
    'recommendations': {'total': 123},
    'reviews': 'html',
    'metacritic': {'url': '...', 'score': 100},
    'controller_support': None or 'full',
    'dlc': 'list of ids',
    'demos': [{'description': '', 'appid': 1234}],  # there are only 2 that have 2
    'drm_notice': str,   # ignore
    
}


GENRES = {
    '1': 'Action',
    '18': 'Sports', 
    '2': 'Strategy', 
    '23': 'Indie',
    '25': 'Adventure',
    '28': 'Simulation',
    '29': 'Massively Multiplayer',
    '3': 'RPG',
    '37': 'Free to Play',
    '4': 'Casual',
    '50': 'Accounting',
    '51': 'Animation & Modeling',
    '52': 'Audio Production',
    '53': 'Design & Illustration',
    '54': 'Education',
    '55': 'Photo Editing',
    '56': 'Software Training',
    '57': 'Utilities',
    '58': 'Video Production',
    '59': 'Web Publishing',
    '70': 'Early Access',
    '9': 'Racing',
}

CATEGORIES = {
    1: 'Multi-player',
    2: 'Single-player',
    6: 'Mods (require HL2)',
    8: 'Valve Anti-Cheat enabled',
    9: 'Co-op',
    10: 'Game demo',
    13: 'Captions available',
    14: 'Commentary available',
    15: 'Stats',
    16: 'Includes Source SDK',
    17: 'Includes level editor',
    18: 'Partial Controller Support',
    19: 'Mods',
    20: 'MMO',
    21: 'Downloadable Content',
    22: 'Steam Achievements',
    23: 'Steam Cloud',
    24: 'Local Co-op',
    25: 'Steam Leaderboards',
    27: 'Cross-Platform Multiplayer',
    28: 'Full controller support',
    29: 'Steam Trading Cards',
    30: 'Steam Workshop',
    31: 'VR Support',
    32: 'Steam Turn Notifications',
    33: 'Native Steam Controller Support'
}

    

# show(2012)
# count_values(b'supported_languages')
# count_keys(type=b'game')
count_values(b'screenshots', 100,)
# read_genres()
# read_categories()
# parse_dates()


# refresh_list()
# mark_and_update()
