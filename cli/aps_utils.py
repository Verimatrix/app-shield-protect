'''Helper utilities'''
import base64
import plistlib
import logging
import os
import shutil
import sys
import requests

from zipfile import is_zipfile, ZipFile

from pyaxmlparser import APK

LOGGER = logging.getLogger(__name__)

def get_config(args):

    config = {}
    config['aws_region'] = 'eu-west-1'
    config['api_gateway_url'] = 'https://aps-api.appshield.verimatrixcloud.net'
    config['access_token_url'] = 'https://api.appshield.verimatrixcloud.net/token'

    if(args.api_gateway_url):
        config['api_gateway_url'] = args.api_gateway_url

    if(args.access_token_url):
        config['access_token_url'] = args.access_token_url


    LOGGER.debug('Constructed config object %s', repr(config))
    return config


def get_os(file):
    '''Deduce the OS based on the file extension'''
    if file.endswith('.apk') or file.endswith('.aab'):
        return 'android'
    if file.endswith('.xcarchive.zip'):
        return 'ios'
    raise ValueError('Unsupported file suffix (not apk or .xcarchive.zip)')

def extract_file_data_from_zip(zipfile, file):
    '''Unzip a particular file from a zip archive'''
    filepath = zipfile.extract(file)
    data = ''
    with open(filepath, 'rb') as file_handle:
        data = base64.b64encode(file_handle.read()).decode('utf-8')
    os.remove(filepath)
    return data

def extract_version_info(file):
    '''Extract application information from the input file to be protected'''
    version_info = {}

    if not file.endswith('.apk') and not file.endswith('.aab') and not file.endswith('.xcarchive.zip'):
        print('Error, input file must be an aab, apk or zipped xcarchive')
        sys.exit(1)

    if not is_zipfile(file):
        print('Error, input file is not in zipped format')
        sys.exit(1)

    # Extract the AndroidManifest.xml or Info.plist from the input zip file
    # and base64 encode it. Delete the file after unzipping.
    zipfile = ZipFile(file)
    if file.endswith('.apk'):
        version_info['androidManifest'] = extract_file_data_from_zip(zipfile,
                                                                     'AndroidManifest.xml')
    elif file.endswith('.aab'):
        version_info['androidManifestProtobuf'] = extract_file_data_from_zip(zipfile,
                                                                             'base/manifest/AndroidManifest.xml')
    else:
        # Get the foldername of the unzipped archive
        dirname = None
        namelist = zipfile.namelist()
        for name in namelist:
            if not name.startswith('.'):
                dirname = os.path.dirname(name)
                break

        for name in namelist:
            if '.app/Info.plist' in name and name.count('.app/') == 1:
                version_info['iosBinaryPlist'] = extract_file_data_from_zip(zipfile, name)

            if '%s/Info.plist' % dirname == name:
                version_info['iosXmlPlist'] = extract_file_data_from_zip(zipfile, name)
        if dirname:
            shutil.rmtree(dirname)

    return version_info


def extract_package_id(file):
    try:
        if file.endswith('.aab'):
            print('Cannot display application package ID for aab files')
            return None

        version_info = extract_version_info(file)
        if 'androidManifest' in version_info:
            apk = APK(file)
            return apk.package
        elif 'iosXmlPlist' in version_info:
            data = version_info['iosXmlPlist']
            plist = plistlib.loads(base64.b64decode(data))
            LOGGER.info('Extracted XML plist: %s', repr(plist))
            return plist['ApplicationProperties']['CFBundleIdentifier']
        elif 'iosBinaryPlist' in version_info:
            data = version_info['iosBinaryPlist']
            plist = plistlib.loads(base64.b64decode(data))
            LOGGER.info('Extracted binary plist: %s', repr(plist))
            return plist['CFBundleIdentifier'].replace('"', '')
        else:
            raise Exception('Unsupported file type')

    except Exception as e:
        print('Failed to extract application package ID')
        LOGGER.warning('extract package id failed: %s', repr(e))
        sys.exit(1)

def authenticate_secret(client_id, client_secret, config):
    '''Authentication using Cognito client credentials. Using a client ID and Client secret.
    Returns an Access Token'''
    msg = '%s:%s' % (client_id, client_secret)
    LOGGER.debug('msg ' + msg)
    auth = base64.b64encode(msg.encode('ascii')).decode('ascii')
    LOGGER.debug('auth ' + auth)

    url = config['access-token-url']
    headers = {}
    headers['Authorization'] = 'Basic %s' % auth
    headers['Content-type'] = 'application/json'

    LOGGER.debug('Authenticating to PMA Portal with client credentials')
    response = requests.post(url, headers=headers, json = {'scope': 'aps'})
    response.raise_for_status()
    resp = response.json()
    LOGGER.debug('Get access token response: %s', resp)

    if 'token' in resp:
        return {'Authorization' : 'Bearer %s' % resp['token']}
    else:
        print('Failed to authenticate, please check client ID and client secret value')
        sys.exit(1)
