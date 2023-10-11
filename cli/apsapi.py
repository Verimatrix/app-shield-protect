# Copyright (c) 2019 - 2021. Verimatrix. All Rights Reserved.
# All information in this file is Verimatrix Confidential and Proprietary.


'''Sending commands to APS API'''
import json
import logging
import os
import shutil
import time
import mimetypes
from datetime import datetime
import dateutil.parser

from aps_utils import (
    get_config, disable_boto_logging, extract_package_id, get_api_gw_url,
    get_os, extract_version_info)
from aps_credentials import authenticate_api_key
from aps_exceptions import ApsException
from aps_requests import ApsRequest

LOGGER = logging.getLogger(__name__)

OPENAPI_VERSION = '1.1.0'

PROTECT_STATES = ['protect_queue', 'protect_in_progress']

# S3 multipart upload has a minimum part size of 5Mb
PART_SIZE=5242880


def upload_data(url, data):
    '''Upload data to S3'''
    return ApsRequest.put(url, data=data)

def construct_headers(token):
    '''Construct HTTP headers to be sent in all requests to APS API endpoint'''
    version = OPENAPI_VERSION
    headers = {}
    headers['Authorization'] = token
    headers['Accept'] = f'application/vnd.aps.appshield.verimatrixcloud.net;version={version}'
    return headers


class ApsApi():
    '''Class for sending commands to APS REST API'''

    def __init__(self, args, **kwargs):

        self.config = get_config(args)
        self.vmx_platform = kwargs.pop('vmx_platform', False)
        self.wait_seconds = kwargs.pop('wait_seconds', 2)
        self.rest_api_id = kwargs.pop('rest_api_id', '')
        self.authenticated = False
        self.headers = None
        self.api_gw_url = get_api_gw_url(self.config, self.rest_api_id)

        verbose_logs = kwargs.pop('verbose_logs', False)
        if not verbose_logs:
            disable_boto_logging()


    def is_authenticated(self):
        '''Have we authenticated'''
        return self.authenticated

    def authenticate_api_key(self, api_key_id, api_key, **kwargs):
        '''Authenticate using API Keys'''
        token = authenticate_api_key(api_key_id, api_key,
                                     self.config, self.vmx_platform, **kwargs)
        self.headers = construct_headers(token)
        self.authenticated = True

    def get_account_info(self):
        '''Return account info'''
        url = f'{self.api_gw_url}/report/account'
        response = ApsRequest.get(url, headers=self.headers)
        LOGGER.debug(f'Response headers: {response.headers}')
        LOGGER.debug(f'Get account info response: {response.json()}')
        return response.json()

    def add_application(self, name, package_id, os_name, permissions, group=None, subscription_type=None):
        '''Add an application'''
        url = f'{self.api_gw_url}/applications'

        body = {}
        body['applicationName'] = name
        body['applicationPackageId'] = package_id
        body['permissionPrivate'] = permissions['private']
        body['permissionUpload'] = False if permissions['private'] else not permissions['no_upload']
        body['permissionDelete'] = False if permissions['private'] else not permissions['no_delete']
        body['os'] = os_name
        if group:
            body['group'] = group
        if subscription_type:
            body['subscriptionType'] = subscription_type

        response = ApsRequest.post(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Post application response: {response.json()}')
        return response.json()

    def update_application(self, application_id, name, permissions):
        '''Update an application'''
        url = f'{self.api_gw_url}/applications/{application_id}'

        body = {}
        body['applicationName'] = name
        body['permissionPrivate'] = permissions['private']
        body['permissionUpload'] = False if permissions['private'] else not permissions['no_upload']
        body['permissionDelete'] = False if permissions['private'] else not permissions['no_delete']
        response = ApsRequest.patch(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Update application response: {response.json()}')
        return response.json()

    def list_applications(self, application_id, group=None, subscription_type=None):
        '''List applications'''
        params = {}

        if subscription_type:
            params['subscriptionType'] = subscription_type

        if application_id:
            url = f'{self.api_gw_url}/applications/{application_id}'
        else:
            url = f'{self.api_gw_url}/applications'
            if group:
                params['group'] = group

        # If not searching by application_id this operation on DynamoDB is Eventually Consistent
        # so wait some time before starting (to ensure system tests using this module behave
        # reliably).
        if not application_id and self.wait_seconds:
            time.sleep(self.wait_seconds)

        response = ApsRequest.get(url, headers=self.headers, params=params)
        LOGGER.debug(f'Response headers: {response.headers}')
        LOGGER.debug(f'Get applications response: {response.json()}')
        return response.json()

    def delete_application(self, application_id):
        '''Delete an aplication'''
        params = {}
        params['id'] = application_id

        url = f'{self.api_gw_url}/applications/{application_id}'

        response = ApsRequest.delete(url, headers=self.headers)
        LOGGER.debug(f'Delete application response: {response.json()}')
        return response.json()

    def list_builds(self, application_id, build_id, subscription_type=None):
        '''List builds'''
        params = {}
        if build_id:
            url = f'{self.api_gw_url}/builds/{build_id}'
        else:
            url = f'{self.api_gw_url}/builds'
            if application_id:
                params['app'] = application_id

        if subscription_type:
            params['subscriptionType'] = subscription_type

        # If not searching by build_id this operation on DynamoDB is Eventually Consistent
        # so wait some time before starting (to ensure system tests using this module behave
        # reliably).
        if not build_id and self.wait_seconds:
            time.sleep(self.wait_seconds)

        response = ApsRequest.get(url, headers=self.headers, params=params)
        builds = response.json()
        LOGGER.debug(f'Listing builds for app_id:{application_id} build_id:{build_id} - {builds}')
        return builds

    def create_build(self, application_id=None, subscription_type=None):
        '''Create a new build'''
        url = f'{self.api_gw_url}/builds'

        # Create a new build
        body = {}
        if application_id:
            body['applicationId'] = application_id
        if subscription_type:
            body['subscriptionType'] = subscription_type
        response = ApsRequest.post(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Post build response: {response.json()}')
        return response.json()


    def set_build_metadata(self, build_id, file):
        '''Set build metadata'''
        version_info = extract_version_info(file)

        # Inform the backend the file is going to be uploaded
        url = f'{self.api_gw_url}/builds/{build_id}/metadata'

        body = {}
        body['os'] = 'ios' if file.endswith('.xcarchive.zip') else 'android'
        body['osData'] = version_info
        response = ApsRequest.put(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Set build metadata response: {response.json()}')
        return response.json()


    def upload_start(self, build_id, file, artifact_type=None):
        '''Start a multipart upload. Returns the upload_id and upload_name'''
        url =  f'{self.api_gw_url}/uploads/{build_id}/start-upload'

        upload_name = os.path.basename(file)

        # mime type
        upload_type = mimetypes.guess_type(file)[0]
        if not upload_type:
            upload_type = 'application/zip'

        params = {
            'uploadName': upload_name,
            'uploadType': upload_type,
        }
        if artifact_type:
            params['artifactType'] = artifact_type

        response = ApsRequest.get(url, headers=self.headers, params=params)
        data = response.json()
        upload_id = data['UploadId']

        return (upload_id, upload_name)

    def upload_complete(self, build_id, upload_id, upload_name, upload_parts, artifact_type=None):
        '''Complete a multipart upload'''
        url =  f'{self.api_gw_url}/uploads/{build_id}/complete-upload'
        body =  {
            'parts': upload_parts,
            'uploadId': upload_id,
            'uploadName': upload_name,
        }
        if artifact_type:
            body['artifactType'] = artifact_type

        response = ApsRequest.post(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Complete upload response: {response.json()}')

    def upload_abort(self, build_id, upload_id, upload_name, message=None, artifact_type=None):
        '''Abort a multipart upload'''
        url =  f'{self.api_gw_url}/uploads/{build_id}/abort-upload'
        body =  {
            'uploadId': upload_id,
            'uploadName': upload_name,
        }
        if message:
            body['message'] = message
        if artifact_type:
            body['artifactType'] = artifact_type

        response = ApsRequest.post(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Abort upload response: {response.json()}')

    def upload_part(self, build_id, upload_id, upload_name, part_number, data):
        '''Upload a single part of the multipart upload. Returns etag information needed
        for the upload complete operation'''
        url =  f'{self.api_gw_url}/uploads/{build_id}/get-upload-url'
        params = {
            'uploadName': upload_name,
            'partNumber': part_number,
            'uploadId': upload_id
        }

        response = ApsRequest.get(url, headers=self.headers, params=params)
        LOGGER.debug(f'Get upload url response: {response.text}')

        # Upload the data
        response = upload_data(response.text, data)

        # Return the Etag and PartNumber
        return {
            'ETag': response.headers['ETag'],
            'PartNumber': part_number
        }

    def multipart_upload(self, build_id, file, artifact_type=None):
        '''Multipart upload method'''
        upload_id = upload_name = None
        try:
            upload_id, upload_name = self.upload_start(build_id, file, artifact_type)

            # Split file into parts. For each part, get an upload url and upload
            # the part. Part numbers start at 1. After uploading each part, save
            # the returned ETag header. We need that when completing the upload.
            parts = []
            part_number = 1
            with open(file, 'rb') as fp:
                while True:
                    data = fp.read(PART_SIZE)
                    if not data:
                        break
                    part = self.upload_part(build_id, upload_id, upload_name, part_number, data)

                    parts.append(part)
                    # Increment the part number and repeat until the file is read.
                    part_number += 1


            # Complete the upload
            self.upload_complete(build_id, upload_id, upload_name, parts, artifact_type)
            return True
        except Exception as e:
            LOGGER.warning(f'Upload method failed: {e}')
            if upload_id and upload_name:
                self.upload_abort(build_id, upload_id, upload_name, artifact_type)
            return False

    def add_build(self, file, application_id=None, set_metadata=True, upload=True, subscription_type=None):
        '''Add a new build'''
        response = self.create_build(application_id, subscription_type)
        if 'errorMessage' in response:
            return response

        build_id = response['id']

        if set_metadata:
            response = self.set_build_metadata(build_id, file)
            if 'errorMessage' in response:
                LOGGER.debug('set build metadata failed, delete build')
                self.delete_build(build_id)
                return response

        # If the application_id is not set, then we do not upload the binary
        # (upload of the binary requires that the build is associated to an app).
        if not application_id or not upload:
            return response

        if not self.multipart_upload(build_id, file):
            LOGGER.debug('upload failed, delete build')
            self.delete_build(build_id)
        return response

    def add_build_without_app(self, file, set_metadata=True, subscription_type=None):
        '''Add a new build that is not yet associated to an application'''

        LOGGER.info(f'Adding new build with subscription type {subscription_type}')

        return self.add_build(file,
                              application_id=None,
                              set_metadata=set_metadata,
                              upload=False,
                              subscription_type=subscription_type)

    def delete_build(self, build_id):
        '''Delete a build'''
        url = f'{self.api_gw_url}/builds/{build_id}'

        response = ApsRequest.delete(url, headers=self.headers)
        LOGGER.debug(f'Delete build response: {response.json()}')
        return response.json()

    def delete_build_ticket(self, build_id, ticket_id):
        '''Delete a Zendesk ticket associated to a build'''
        url = f'{self.api_gw_url}/builds/{build_id}'

        params = {}
        params['cmd'] = 'delete-ticket'
        params['ticket'] = ticket_id
        response = ApsRequest.patch(url, headers=self.headers, params=params)
        LOGGER.debug(f'Delete build ticket response: {response.json()}')
        return response.json()

    def get_build_ticket(self, build_id, ticket_id):
        '''Get the Zendesk ticket details'''
        url = f'{self.api_gw_url}/builds/{build_id}'

        params = {}
        params['ticket'] = ticket_id

        response = ApsRequest.get(url, headers=self.headers, params=params)
        LOGGER.debug(f'Get build ticket response: {response.json()}')
        return response.json()

    def protect_start(self, build_id):
        '''Initiate build protection'''
        url = f'{self.api_gw_url}/builds/{build_id}'

        params = {}
        params['cmd'] = 'protect'

        response = ApsRequest.patch(url, headers=self.headers, params=params)
        LOGGER.debug(f'Protect start response: {response.json()}')
        return response.json()

    def protect_get_status(self, build_id):
        '''Get the protection status of a build'''
        return self.list_builds(None, build_id, None)

    def protect_cancel(self, build_id):
        '''Cancel a protection job'''
        url = f'{self.api_gw_url}/builds/{build_id}'

        params = {}
        params['cmd'] = 'cancel'

        response = ApsRequest.patch(url, headers=self.headers, params=params)
        LOGGER.debug(f'Protect cancel response: {response.json()}')
        return response.json()

    def protect_download(self, build_id):
        '''Download a protected build file'''
        # Request a S3 presigned URL for the download
        url = f'{self.api_gw_url}/builds/{build_id}'

        params = {}
        params['url'] = 'protected'

        response = ApsRequest.get(url, headers=self.headers, params=params)
        LOGGER.debug(f'Protect get download URL, response: {response.text}')

        # Now download the protected binary.
        url = response.text
        local_filename = url.split('/')[-1]
        local_filename = local_filename.split('?')[0]
        LOGGER.info('Starting download of protected file')

        response = ApsRequest.get(url, stream=True)
        LOGGER.debug(f'Download protection file response: {response}')
        with open(local_filename, 'wb') as file_handle:
            shutil.copyfileobj(response.raw, file_handle)
        LOGGER.info(f'Protected file downloaded to {local_filename}')

        result_file = open('protect_result.txt', 'w')
        result_file.write(local_filename)
        result_file.close()

    def add_build_to_application(self, build_id, application_id):
        '''Associate a build to an application'''
        url = f'{self.api_gw_url}/builds/{build_id}/app'

        body = {}
        body['applicationId'] = application_id

        response = ApsRequest.put(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Add build to application response: {response.json()}')
        return response.json()

    def protect_build(self, build_id):
        '''High level protect build command.
        This operation does the following
        - protect_start
        - poll protection state (protect_get_status) until protection is completed'''
        # Start protection
        response = self.protect_start(build_id)
        if 'errorMessage' in response:
            LOGGER.debug('protection start call failed, delete build')
            self.delete_build(build_id)
            return False


        while True:
            build = self.protect_get_status(build_id)

            if not 'state' in build.keys():
                LOGGER.info(f'Failed to get protect status for build {build_id}')
                LOGGER.info(build)
                return False

            if build['state'] not in PROTECT_STATES:
                LOGGER.info('Protection complete')
                break
            if build['state'] == 'protect_queue':
                LOGGER.info('In protect queue..')
            else:
                if 'progressData' in build:
                    LOGGER.info(f'Protecting {build["progressData"]["progress"]} complete')
            time.sleep(10)

        return (build['state'] == 'protect_done')


    def protect(self, file, subscription_type=None, signing_certificate=None, mapping_file=None):
        '''High level protect command.
        This operation does the following
        - add_build
        - protect_start
        - poll protection state (protect_get_status) until protection is completed
        - protect_download'''

        # First add the build
        build = self.add_build_without_app(file, subscription_type=subscription_type)
        if 'errorMessage' in build:
            LOGGER.error(f'Failed to add new build {build["errorMessage"]}')
            return False

        application_package_id = build['applicationPackageId']
        os_type = get_os(file)

        applications = self.list_applications(application_id=None,
                                              group=None,
                                              subscription_type=subscription_type)
        application = None

        # Check if we have an app for this build (by searching for a matching
        # applicationPackageId)
        for app in applications:
            if app['applicationPackageId'] == application_package_id \
               and app['os'] == os_type:
                application = app
                break

        # If no application for the build exists then create a new app.
        # Take the applicationName from the package id and use default permissive permissions
        if not application:
            permissions = {}
            permissions['private'] = False
            permissions['no_upload'] = False
            permissions['no_delete'] = False

            application = self.add_application(application_package_id,
                                               application_package_id,
                                               os_type,
                                               permissions,
                                               subscription_type=subscription_type)
            if 'errorMessage' in application:
                LOGGER.error(f'Failed to add new application {application["errorMessage"]}')
                return False

        self.add_build_to_application(build['id'], application['id'])

        if signing_certificate:
            self.set_signing_certificate(application['id'], signing_certificate)
        if mapping_file:
            self.set_mapping_file(build['id'], mapping_file)

        # Upload the binary
        if not self.multipart_upload(build['id'], file):
            LOGGER.debug('upload failed, delete build')
            self.delete_build(build['id'])
            return False

        # Start protection

        if not self.protect_build(build['id']):
            LOGGER.info(f'Protection failed with build id:{build["id"]}')
            return False

        # Download the protected app on success.
        self.protect_download(build['id'])
        # This line is parsed by test-events-android to extract the build id. Do not change
        LOGGER.info(f'Protection succeeded with build id:{build["id"]}')

        return True

    def get_build_artifacts(self, build_id):
        '''Get build artifacts'''

        url = f'{self.api_gw_url}/report/artifacts?buildId={build_id}'

        response = ApsRequest.get(url, headers=self.headers)

        outdir = os.getcwd() + os.sep + build_id
        shutil.rmtree(outdir, ignore_errors=True)
        os.mkdir(outdir)

        artifact_urls = response.json()
        for url in artifact_urls:
            local_filename = url.split('/')[-1]
            local_filename = local_filename.split('?')[0]
            LOGGER.info(f'Downloading artifact {local_filename}')
            local_filename = outdir + os.sep + local_filename
            response = ApsRequest.get(url, stream=True)
            with open(local_filename, 'wb') as file_handle:
                shutil.copyfileobj(response.raw, file_handle)
        LOGGER.info(f'Build artifacts downloaded to {outdir}')


    def get_statistics(self, start, end):
        '''Get APS statistics'''
        start_time = dateutil.parser.parse(start)
        if end:
            end_time = dateutil.parser.parse(end)
        else:
            end_time = datetime.now()

        params = {}

        url = f'{self.api_gw_url}/report/statistics?start={start_time}&end={end_time}'
        response = ApsRequest.get(url, headers=self.headers, params=params)
        return response.json()

    def display_application_package_id(self, file):
        '''Extract the package id from the input file'''
        return extract_package_id(file)

    def set_protection_configuration(self, application_id, file):
        '''Set protection configuration for an application'''
        url = f'{self.api_gw_url}/applications/{application_id}/protection-configuration'

        body = {}
        if file:
            with open(file, 'rb') as file_handle:
                body['configuration'] = json.load(file_handle)
        response = ApsRequest.put(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Set protection configuration response: {response.json()}')
        return response.json()


    def set_signing_certificate(self, application_id, file):
        '''Set signing certificate for an application'''

        url = f'{self.api_gw_url}/applications/{application_id}/signing-certificate'

        body = {}
        if file:
            with open(file, 'r') as file_handle:
                body['certificate'] = file_handle.read()
                body['certificateFileName'] = os.path.basename(file)
        LOGGER.info(body)
        response = ApsRequest.put(url, headers=self.headers, data=json.dumps(body))
        LOGGER.debug(f'Set signing certificate response: {response.json()}')
        return response.json()

    def set_mapping_file(self, build_id, file):
        '''Set mapping for a build'''
        return self.multipart_upload(build_id, file, 'MAPPING_FILE')

    def get_sail_config(self, os_type, version):
        '''Get SAIL configuration'''
        url = f'{self.api_gw_url}/sail_config'

        params = {}
        params['os'] = os_type
        if version:
            params['version'] = version

        response = ApsRequest.get(url, headers=self.headers, params=params)
        config = response.json()
        LOGGER.debug('Get SAIL configuration')
        return config

    def get_version(self):
        '''Get version'''
        url = f'{self.api_gw_url}/version'
        response = ApsRequest.get(url, headers=self.headers)
        return response.json()
