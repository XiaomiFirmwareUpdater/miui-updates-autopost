# MIUI Updates auto-posting
#### By [yshalsager](https://t.me/yshalsager)

A python 3 script, made for telegram channels admins to post MIUI updates for a device automatically. It uses [miui-updates-tracker](https://github.com/XiaomiFirmwareUpdater/miui-updates-tracker) public JSON files to fetch certain device updates and post it to a telegram channel.

### How to use:

- Make sure you have python3.6+ installed.
- Install the required packages.
```
pip3 install -r requirements.txt
```
- Copy the bot config file and rename it to config.json, place your bot API TOKEN, Telegram channel username or id, and device codename at placeholders.
It should be like this:
``` json
{
 "tg_bot_token": "xxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxx",
 "tg_channel": "-100xxxxxxxxx",
 "codename": "sagit"
}
```
- Run the bot using `python3 auto_post.py`
- To make the bot runs continuously you need to set up a cronjon on your own.

