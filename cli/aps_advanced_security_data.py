import base64
import datetime
import hashlib
import hmac
import json
import platform
import time
import uuid

VERSION = 'JS20171115'

def get_user_agent():
    return 'custom-user-agent'

def get_platform():
    if platform.system() == 'Darwin':
        return 'MacIntel'
    if platform.system() == 'Linux':
        return 'Linux'
    return 'Win32'

def get_client_timezone():
    offset = -time.timezone

    sign = '-' if offset < 0 else ''
    n = offset if offset > 0 else offset * -1
    hours = int(offset / 3600)
    minutes = int(offset % 3600)
    return f'{sign}0{hours}:0{minutes}'

def get_device_id():
    return hex(uuid.getnode())

def get_device_language():
    return 'en-US'

def generate_payload(username, user_pool_id):
    language = get_device_language()
    user_agent = get_user_agent()
    data = {
        'contextData': {
            'UserAgent': user_agent,
            'DeviceId': get_device_id(),
            'DeviceLanguage': language,
            'DeviceFingerprint': f'{user_agent}WebKit built-in PDF:{language}',
            'DevicePlatform': get_platform(),
            'ClientTimezone': get_client_timezone(),
        },
        'username': username,
        'userPoolId': user_pool_id,
        'timestamp':  str(round(time.time() * 1000))
    }
    return json.dumps(data, separators=(',', ':'))


def generate_signature(payload, user_pool_client_id, version):
    key = user_pool_client_id.encode()

    mac = hmac.new(key, digestmod='sha256')
    mac.update(version.encode())
    mac.update(payload.encode())
    return base64.b64encode(mac.digest()).decode('ascii')
