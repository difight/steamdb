

import requests

APP_LIST_URL = "http://api.steampowered.com/ISteamApps/GetAppList/v0001/"

APPID_URL = "http://store.steampowered.com/api/appdetails"
APPID_URL_APP_ID_PARAM = "appids"
APPID_URL_COUNTRY_PARAM = "cc"


# TODO: add DB integration
# TODO: add package information


def get_steam_apps_by_name():

    games = get_steam_apps_list()
    
    return {g['appid']: g['name'] for g in games}


def get_steam_apps_by_id():

    games = get_steam_apps_list()

    return {g['appid']: g['name'] for g in games}
    

def get_steam_apps_list():
    r = requests.get(APP_LIST_URL)

    applist = r.json()['applist']
    apps = applist['apps']
    app = apps['app']

    return app

def get_app_info(app_id, country_code='de'):

    r = requests.get(APPID_URL, {
        APPID_URL_APP_ID_PARAM: app_id,
        APPID_URL_COUNTRY_PARAM: country_code,
    })

    app_result = r.json().get(str(app_id), {})

    if app_result.get('success'):
        return app_result.get('data')
    else:
        return None


