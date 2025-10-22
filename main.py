import requests
import os
import json
from datetime import datetime
from pythonping import ping
import time
from wakeonlan import send_magic_packet


def log(message):
    with open("log.txt", "a") as f:
        print(f"{datetime.now()} - {message}")
        f.write(f"{datetime.now()} - {message}\n")


def try_request(url):
    try:
        log(f"Trying to request {url}")
        response = requests.get("http://" + url, timeout=5)
        if response.status_code == 200:
            log(f"Request to {url} succeeded")
            return True
        else:
            log(f"Request to {url} failed with status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        log(f"Request to {url} failed with exception: {e}")
        print(f"Error: {e}")
        return False


try:
    weekday_today = datetime.now().strftime("%A").lower()
    json_data = json.load(open("schedule.json"))
    today = json_data[weekday_today]
    now = datetime.now().strftime("%H:%M")


    today_on = today["on"]
    today_off = today["off"]
    is_between = today_on <= now <= today_off

    if is_between:
        for interval in today.get("interval", []):
            if interval[0] <= now <= interval[1]:
                log(f"Current time {now} is within the interval {interval[0]} - {interval[1]}. Shutting down computer.")
                is_between = False
                break


    attempt = 0

    if is_between and not ping(json_data["computer"], count=1).success():
        if try_request(rf'{json_data["esp"]}{json_data['url']['contactor-on']}'):
            while attempt < 10 and not ping(json_data["computer"], count=1).success():
                log(rf"Attempting to push computer on by WOL, attempt {attempt + 1}.")
                # try_request(rf'{json_data["esp"]}{json_data['url']['computer-push']}')
                send_magic_packet('20-04-0F-FF-A1-03')
                attempt += 1
                time.sleep(40)

            else:
                if attempt > 3:
                    log("Attempted to push computer on 3 times, stopping.")
                elif ping(json_data["computer"], count=1).success():
                    log("Computer is now on.")

        else:
            log("Failed to turn on the ESP.")



    else:
        if not is_between:
            log("Not between the scheduled times.")
            attempt = 0
            while attempt <= 3 and ping(json_data["computer"], count=1).success():
                
                log(rf"Attempting to shutdown computer, attempt {attempt + 1}.")
                try:
                    os.system(rf'shutdown /s /m \\{json_data["computer"]} /t 0')
                    log("Shutdown command sent.")

                except Exception as e:
                    log(f"Error sending shutdown command: {e}")

                attempt += 1
                time.sleep(90)
            else:
                log("Finished shutdown attempts.")
                if attempt > 3:
                    log("Attempted to shutdown computer on 3 times, stopping.")
                elif not ping(json_data["computer"], count=1).success():
                    log("Computer is now off.")
                    log("Trying to turn off the contactor.")
                    try_request(rf'{json_data["esp"]}{json_data["url"]["contactor-off"]}')

        elif ping(json_data["computer"], count=1).success():
            log("Computer is already on.")
except Exception as e:
    log(f"An fatal error occurred: {e}")