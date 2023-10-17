# Copyright (c) 2019 - 2021. Verimatrix. All Rights Reserved.
# All information in this file is Verimatrix Confidential and Proprietary.
import base64
import logging

from aps_requests import ApsRequest
from aps_exceptions import ApsException

LOGGER = logging.getLogger(__name__)


###########################################################################


def authenticate_api_key(api_key_id, api_key, config, vmx_platform, **kwargs):
    '''Authentication using an API Key. sReturns an token that can be used as a HTTP authorization header'''

    resp = {}
    if vmx_platform:
        LOGGER.debug('Authenticating with platform API key')
        url = config['platform-access-token-url']
        body = {}
        body['userEmail'] = api_key_id
        body['apiKey'] = api_key

        response = ApsRequest.post(url, json={'body': body})
        resp = response.json()
    else:
        LOGGER.debug('Authenticating with client credentials')
        msg = f'{api_key_id}:{api_key}'
        auth = base64.b64encode(msg.encode('ascii')).decode('ascii')

        url = config['access-token-url']
        headers = {}
        headers['Authorization'] = f'Basic {auth}'
        headers['Content-type'] = 'application/json'

        scope = kwargs.pop('scope', 'aps')
        response = ApsRequest.post(url, headers=headers, json={'scope': scope})
        resp = response.json()

    LOGGER.debug(f'Get access token response: {resp}')

    if not 'token' in resp:
        LOGGER.error(
            'Failed to authenticate, please check client ID and client secret value')
        raise ApsException(
            'Failed to authenticate, please check client ID and client secret value')
    return f'Bearer {resp["token"]}'