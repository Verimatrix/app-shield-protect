# Copyright (c) 2019 - 2021. Verimatrix. All Rights Reserved.
# All information in this file is Verimatrix Confidential and Proprietary.
import base64
import logging

from aps_requests import ApsRequest
from aps_exceptions import ApsException

LOGGER = logging.getLogger(__name__)


###########################################################################


def authenticate_api_key(api_key_id, api_key, config, vmx_platform, **kwargs):
    '''Authentication using an API Key. Uses an API Key ID and API Key.
        Returns an token that can be used as a HTTP authorization header'''
    if vmx_platform:
        raise ApsException('Client ID and Secret authentication not supported for Verimatrix Platform')

    msg = f'{api_key_id}:{api_key}'
    auth = base64.b64encode(msg.encode('ascii')).decode('ascii')

    url = config['access-token-url']
    headers = {}
    headers['Authorization'] = f'Basic {auth}'
    headers['Content-type'] = 'application/json'

    LOGGER.debug('Authenticating with client credentials')

    scope = kwargs.pop('scope', 'aps')
    response = ApsRequest.post(url, headers=headers, json = {'scope': scope})
    resp = response.json()
    #LOGGER.debug(f'Get access token response: {resp}')

    if not 'token' in resp:
        LOGGER.error('Failed to authenticate, please check client ID and client secret value')
        raise ApsException('Failed to authenticate, please check client ID and client secret value')
    return f'Bearer {resp["token"]}'
