#!/usr/bin/env python3.7
"""MIUI Updates telegram auto-poster"""

import json
from glob import glob
from os import makedirs, rename, remove
from requests import get, post

# read config
try:
    with open('config.json', 'r') as config:
        try:
            CONFIG = json.load(config)
        except json.JSONDecodeError:
            print('JSON config is incorrect, please check it using jsonlint.com!')
            exit(10)
except FileNotFoundError:
    print('config.json is missing!\n'
          'Please copy "config.json.example" and rename it to "config.json"'
          'and change the variables with yours!')
    exit(20)
try:
    TG_TOKEN = CONFIG['tg_bot_token']
except KeyError:
    print('tg_bot_token is missing! Please add it to config file!')
    exit(31)
try:
    TG_CHANNEL = CONFIG['tg_channel']
except KeyError:
    print('tg_channel is missing! Please add it to config file!')
    exit(32)
try:
    CODENAME = CONFIG['codename']
    PATH = f"data/{CODENAME}"
except KeyError:
    print('codename is missing! Please add it to config file!')
    exit(33)

CHANGES = []


def initialize():
    """
    creates required folders and copy old files
    """
    makedirs("data", exist_ok=True)
    makedirs(PATH, exist_ok=True)
    for file in glob(f'{PATH}/*.json'):
        if 'old_' in file:
            continue
        name = 'old_' + file.split('/')[-1]
        rename(file, '/'.join(file.split('/')[:-1]) + '/' + name)


def load_data():
    """
    loads latest MIUI updates from MIUI Updates Tracker json files
    """
    latest_stable_recovery = get(
        "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/" +
        "stable_recovery/stable_recovery.json").json()
    latest_weekly_recovery = get(
        "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/" +
        "weekly_recovery/weekly_recovery.json").json()
    latest_stable_fastboot = get(
        "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/" +
        "stable_fastboot/stable_fastboot.json").json()
    latest_weekly_fastboot = get(
        "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/" +
        "weekly_fastboot/weekly_fastboot.json").json()
    return latest_stable_recovery, latest_stable_fastboot,\
        latest_weekly_recovery, latest_weekly_fastboot


def write_json(name, data):
    """
    write fetched data to json file
    """
    filename = '{}/{}.json'.format(PATH, str(name))
    with open(filename, 'w') as output:
        json.dump(data, output, indent=1)


def diff(name):
    """
    compare json files
    """
    try:
        with open(f'{PATH}/{name}.json', 'r') as new,\
                open(f'{PATH}/old_{name}.json', 'r') as old_data:
            latest = json.load(new)
            old = json.load(old_data)
            first_run = False
    except FileNotFoundError:
        print(f"Can't find old {name} files, skipping")
        first_run = True
    if first_run is False:
        for new_, old_ in zip(latest, old):
            if not new_['version'] == old_['version']:
                CHANGES.append(new_)


def rolledback_check(file, version, branch):
    """
    check if this update is rolled-back
    :return:
    """
    rolled_back = False
    try:
        old_data = json.loads(get(
            "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/" +
            "xiaomifirmwareupdater.github.io/master/data/devices/" +
            "full/{}.json".format(CODENAME.split("_")[0])).content)
    except json.decoder.JSONDecodeError:
        print(f"Working on {CODENAME} for the first time!")
        old_data = []
    if 'MI' in file or 'Global' in file:
        region = 'Global'
    else:
        region = 'China'
    if branch == 'Stable':
        all_versions = [i for i in old_data if i['branch'] == 'stable']
    else:
        all_versions = [i for i in old_data if i['branch'] == 'weekly']
    check = [i for i in all_versions if i['versions']['miui'] == version and i['type'] == region]
    if check:
        print("{}: {} is rolled back ROM!".format(CODENAME, version))
        rolled_back = True
    return rolled_back


def tg_post(message):
    """
    post message to telegram
    """
    params = (
        ('chat_id', TG_CHANNEL),
        ('text', message),
        ('parse_mode', "Markdown"),
        ('disable_web_page_preview', "yes")
    )
    telegram_url = "https://api.telegram.org/bot" + TG_TOKEN + "/sendMessage"
    telegram_req = post(telegram_url, params=params)
    telegram_status = telegram_req.status_code
    if telegram_status == 200:
        print(f"{CODENAME}: Telegram Message sent")
    elif telegram_status == 400:
        print("Bad recipient / Wrong text format")
    elif telegram_status == 401:
        print("Wrong / Unauthorized token")
    else:
        print("Unknown error")
        print("Response: " + telegram_req.reason)


def tg_message(update):
    """
    generates telegram message
    """
    android = update['android']
    codename = update['codename'].split('_')[0]
    device = update['device']
    download = update['download']
    filename = update['filename']
    version = update['version']
    if 'V' in version:
        branch = 'Stable'
    else:
        branch = 'Weekly'
    if 'eea_global' in filename or 'EU' in filename:
        region = 'EEA Global'
    elif 'in_global' in filename or 'IN' in filename:
        region = 'India'
    elif 'ru_global' in filename or 'RU' in filename:
        region = 'Russia'
    elif 'global' in filename or 'MI' in filename:
        region = 'Global'
    else:
        region = 'China'
    if '.tgz' in filename:
        rom_type = 'Fastboot'
    else:
        rom_type = 'Recovery'
    rolled_back = rolledback_check(filename, version, region)
    message = ''
    if rolled_back:
        message += f'Rolled back {branch} {rom_type} update!\n'
    else:
        message += f"New {branch} {rom_type} update available!\n"
    message += f"*Device:* {device} \n" \
        f"*Codename:* #{codename} \n" \
        f"*Region:* {region} \n" \
        f"*Version:* `{version}` \n" \
        f"*Android:* {android} \n" \
        f"*Download*: [Here]({download}) \n" \
        "@MIUIUpdatesTracker | @XiaomiFirmwareUpdater"
    tg_post(message)


def main():
    """
    Loads, compare, and post MIUI updates to a telegram channel
    """
    initialize()
    latest_stable_recovery, latest_stable_fastboot, \
        latest_weekly_recovery, latest_weekly_fastboot = load_data()
    stable_recovery = [i for i in latest_stable_recovery if CODENAME in i['codename']]
    stable_fastboot = [i for i in latest_stable_fastboot if CODENAME in i['codename']]
    weekly_recovery = [i for i in latest_weekly_recovery if CODENAME in i['codename']]
    weekly_fastboot = [i for i in latest_weekly_fastboot if CODENAME in i['codename']]
    roms = {'stable_recovery': stable_recovery, 'stable_fastboot': stable_fastboot,
            'weekly_recovery': weekly_recovery, 'weekly_fastboot': weekly_fastboot}
    for name, data in roms.items():
        write_json(name, data)
        diff(name)
    if CHANGES:
        for update in CHANGES:
            tg_message(update)
    else:
        print('No new updates found!')
    for file in glob(f'{PATH}/old_*.json'):
        remove(file)


if __name__ == '__main__':
    main()
