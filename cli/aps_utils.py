# Copyright (c) 2019 - 2021. Verimatrix. All Rights Reserved.
# All information in this file is Verimatrix Confidential and Proprietary.

'''Helper utilities'''
import base64
import plistlib
import logging
import os
import shutil
import sys

from zipfile import is_zipfile, ZipFile

from pyaxmlparser import APK

from aps_exceptions import ApsException

LOGGER = logging.getLogger(__name__)

def disable_boto_logging():
    '''Disable logging from third party modules'''
    modules_to_disable = ['boto', 's3transfer', 'urllib3', 'boto3', 'botocore']
    for name in logging.Logger.manager.loggerDict:
        if name in modules_to_disable:
            logging.getLogger(name).setLevel(logging.CRITICAL)

def get_config(args):

    config = {}
    config['aws_region'] = 'eu-west-1'
    config['api_gateway_url'] = 'https://aps-api.appshield.verimatrixcloud.net'
    config['access-token-url'] = 'https://api.appshield.verimatrixcloud.net/token'
    config['platform-access-token-url'] = 'https://ssoapi-ng.platform.verimatrixcloud.net/v1/token'

    if(args.api_gateway_url):
        config['api_gateway_url'] = args.api_gateway_url

    if(args.access_token_url):
        if (args.platform):
            config['platform-access-token-url'] = args.access_token_url
        else:
            config['access-token-url'] = args.access_token_url

    LOGGER.debug('Constructed config object %s', repr(config))
    return config

def get_api_gw_url(config, rest_api_id):
    ''''Returns the API Gateway URL to use for a specific path'''
    return config['api_gateway_url'].format(rest_api_id=rest_api_id)


def get_os(file):
    '''Deduce the OS based on the file extension'''
    if file.endswith('.apk') or file.endswith('.aab'):
        return 'android'
    if file.endswith('.xcarchive.zip'):
        return 'ios'
    raise ApsException('Unsupported file suffix (not apk or .xcarchive.zip)')

def extract_file_data_from_zip(zipfile, file):
    '''Unzip a particular file from a zip archive'''
    filepath = zipfile.extract(file)
    data = ''
    with open(filepath, 'rb') as file_handle:
        data = base64.b64encode(file_handle.read()).decode('utf-8')
    os.remove(filepath)
    return data

ALLOWED_SUFFIXES = ['.apk', '.aab', '.xcarchive.zip']

def extract_version_info(file):
    '''Extract application information from the input file to be protected'''
    version_info = {}

    suffix_ok = False
    for _, suffix in enumerate(ALLOWED_SUFFIXES):
        if file.endswith(suffix):
            suffix_ok = True
    if not suffix_ok:
        LOGGER.critical('Error, input file must be an aab, apk or zipped xcarchive')
        raise ApsException('Error, input file must be an aab, apk or zipped xcarchive')

    if not is_zipfile(file):
        LOGGER.critical('Error, input file is not in zipped format')
        raise ApsException('Error, input file is not in zipped format')

    # Extract the AndroidManifest.xml or Info.plist from the input zip file
    # and base64 encode it. Delete the file after unzipping.
    zipfile = ZipFile(file)
    if file.endswith('.apk'):
        version_info['androidManifest'] = extract_file_data_from_zip(zipfile,
                                                                     'AndroidManifest.xml')
    elif file.endswith('.aab'):
        version_info['androidManifestProtobuf'] = \
            extract_file_data_from_zip(zipfile, 'base/manifest/AndroidManifest.xml')
    else:
        # Get the folder name of the unzipped archive
        dirname = None
        namelist = zipfile.namelist()
        for name in namelist:
            if not name.startswith('.'):
                dirname = os.path.dirname(name)
                break

        for name in namelist:
            if '.app/Info.plist' in name and name.count('.app/') == 1:
                version_info['iosBinaryPlist'] = extract_file_data_from_zip(zipfile, name)

            if f'{dirname}/Info.plist' == name:
                version_info['iosXmlPlist'] = extract_file_data_from_zip(zipfile, name)
        if dirname:
            shutil.rmtree(dirname)

    return version_info


def extract_package_id(file):
    '''Extract application package ID from binary file'''
    try:
        if file.endswith('.aab'):
            LOGGER.error('Cannot display application package ID for aab files')
            return None

        version_info = extract_version_info(file)
        if 'androidManifest' in version_info:
            apk = APK(file)
            return apk.package
        elif 'iosXmlPlist' in version_info:
            data = version_info['iosXmlPlist']
            plist = plistlib.loads(base64.b64decode(data))
            LOGGER.info(f'Extracted XML plist: {plist}')
            return plist['ApplicationProperties']['CFBundleIdentifier']
        elif 'iosBinaryPlist' in version_info:
            data = version_info['iosBinaryPlist']
            plist = plistlib.loads(base64.b64decode(data))
            LOGGER.info(f'Extracted binary plist: {plist}')
            return plist['CFBundleIdentifier'].replace('"', '')
        else:
            raise ApsException('Unsupported file type')
    except Exception as e:
        LOGGER.error('Failed to extract application package ID: {e}')
        raise ApsException(e) from e


LOGGER = logging.getLogger(__name__)

def setup_logging(log_level):
    '''Setup logging'''
    LOGGER.setLevel(log_level)
