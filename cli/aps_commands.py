'''Sending commands to AWS API Gateway'''
import js2py
import json
import logging
import os
import shutil
import time
from datetime import datetime
import dateutil.parser

import requests

from aps_utils import extract_version_info, get_os, extract_package_id
from common import common

LOGGER = logging.getLogger(__name__)

PROTECT_STATES = ['protect_queue', 'protect_in_progress']

def retry_on_connection_error(method, max_retries=5):
    '''Execute the input method. Retries on ConnectionError exceptions'''
    retries = 0
    while retries < max_retries:
        try:
            return method()
        except requests.exceptions.ConnectionError as e:
            LOGGER.warning('Upload method failed: %s', repr(e))
            retries += 1
    raise Exception("Maximum retries exceeded")

def check_requests_response(response):
    '''Check response from requests call. If there is an error message coming from
    APS backend then return it, otherwise raise an exception'''
    if 'Content-Type' in response.headers and response.headers['Content-Type'] == 'application/json':
        if 'errorMessage' in response.json():
            LOGGER.warning(common.getSimpleErrorMessage(response.json()['errorMessage']))
            return
    response.raise_for_status()

def upload(url, file):
    '''Upload a file to S3. Retries on ConnectionError exceptions'''
    def try_upload():
        with open(file, 'rb') as file_handle:
            requests.put(url, data=file_handle)
            return None
    retry_on_connection_error(try_upload)

class ApsCommands():
    '''Class for sending commands to AWS API Gateway'''

    def __init__(self, headers, config, using_client_secret, eventually_consistent_command_wait_seconds=2):
        self.headers = headers
        self.config = config
        self.using_client_secret = using_client_secret
        self.eventually_consistent_command_wait_seconds = eventually_consistent_command_wait_seconds

    def get_api_gw_url(self, path):
        ''''Returns the API Gateway URL to use for a specific path'''
        apiPath = 'api/' if self.using_client_secret else ''
        return '%s/%s%s' % (self.config['api_gateway_url'], apiPath, path)

    def get_account_info(self):
        '''Return account info'''
        url = '%s/account' % self.get_api_gw_url('report')
        response = requests.get(url, headers=self.headers)
        check_requests_response(response)
        LOGGER.debug('Response headers: %s', repr(response.headers))
        LOGGER.debug('Get account info response: %s', response.json())
        return response.json()

    def add_application(self, name, package_id, os_name, permissions, group=None):
        '''Add an application'''
        url = self.get_api_gw_url('applications')

        body = {}
        body['applicationName'] = name
        body['applicationPackageId'] = package_id
        body['permissionPrivate'] = permissions['private']
        body['permissionUpload'] = False if permissions['private'] else not permissions['no_upload']
        body['permissionDelete'] = False if permissions['private'] else not permissions['no_delete']
        body['os'] = os_name
        if group:
            body['group'] = group
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        check_requests_response(response)
        LOGGER.debug('Post application response: %s', response.json())
        return response.json()

    def update_application(self, application_id, name, permissions):
        '''Update an application'''
        url = '%s/%s' % (self.get_api_gw_url('applications'), application_id)

        body = {}
        body['applicationName'] = name
        body['permissionPrivate'] = permissions['private']
        body['permissionUpload'] = False if permissions['private'] else not permissions['no_upload']
        body['permissionDelete'] = False if permissions['private'] else not permissions['no_delete']
        response = requests.patch(url, headers=self.headers, data=json.dumps(body))
        check_requests_response(response)
        LOGGER.debug('Update application response: %s', response.json())
        return response.json()

    def list_applications(self, application_id, group=None, wait_ec=True):
        '''List applications'''
        params = {}

        if application_id:
            url = '%s/%s' % (self.get_api_gw_url('applications'), application_id)
        else:
            url = self.get_api_gw_url('applications')
            if group:
                params['group'] = group

        # If not searching by application_id this operation on DynamoDB is Eventually Consistent 
        # so wait some time before starting (to ensure system tests using this module behave
        # reliably).
        if not application_id and self.eventually_consistent_command_wait_seconds:
            time.sleep(self.eventually_consistent_command_wait_seconds)

        response = requests.get(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Get applications response: %s', response.json())

        return response.json()

    def delete_application(self, application_id):
        '''Delete an aplication'''
        params = {}
        params['id'] = application_id

        url = '%s/%s' % (self.get_api_gw_url('applications'), application_id)

        response = requests.delete(url, headers=self.headers)
        check_requests_response(response)
        LOGGER.debug('Delete application response: %s', response.json())
        return response.json()

    def list_builds(self, application_id, build_id):
        '''List builds'''
        params = {}
        if build_id:
            url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)
        else:
            url = self.get_api_gw_url('builds')
            if application_id:
                params['app'] = application_id

        # If not searching by build_id this operation on DynamoDB is Eventually Consistent 
        # so wait some time before starting (to ensure system tests using this module behave
        # reliably).
        if not build_id and self.eventually_consistent_command_wait_seconds:
            time.sleep(self.eventually_consistent_command_wait_seconds)

        response = requests.get(url, headers=self.headers, params=params)
        check_requests_response(response)
        builds = response.json()
        LOGGER.debug('Listing builds for app_id:%s build_id:%s - %s',
                     application_id, build_id, repr(builds))
        return builds

    def create_build(self, application_id=None):
        '''Create a new build'''
        url = self.get_api_gw_url('builds')

        # Create a new build
        body = {}
        if application_id:
            body['applicationId'] = application_id
        response = requests.post(url, headers=self.headers, data=json.dumps(body))
        check_requests_response(response)
        LOGGER.debug('Post build response: %s', response.json())
        return response.json()


    def set_build_metadata(self, build_id, file):
        '''Set build metadata'''
        version_info = extract_version_info(file)

        # Inform the backend the file is going to be uploaded
        url = '%s/%s/metadata' % (self.get_api_gw_url('builds'), build_id)

        body = {}
        body['os'] = 'ios' if file.endswith('.xcarchive.zip') else 'android'
        body['osData'] = version_info
        response = requests.put(url, headers=self.headers, data=json.dumps(body))
                                  
        check_requests_response(response)
        LOGGER.debug('Set build metadata response: %s', response.json())
        return response.json()

    def upload_build(self, build_id, file):
        '''Upload a build to S3'''
        # Next upload the binary apk/xcarchive
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['url'] = 'raw'
        params['uploadname'] = os.path.basename(file)

        response = requests.get(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Get upload raw URL response: %s', response.text)

        upload(response.text, file)
        return {}

    def upload_build_success(self, build_id, file):
        '''Inform the backend the build file is uploaded successfully to S3'''
        # Inform the backend the build file is uploaded
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)
        params = {}
        params['cmd'] = 'upload-success'

        response = requests.patch(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Upload build success response: %s', response.json())
        return response.json()

    def upload_build_failed(self, build_id, message):
        '''Inform the backend the build upload failed'''
        # Inform the backend the upload failed
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['cmd'] = 'upload-failed'
        params['message'] = message

        response = requests.patch(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Upload build failed response: %s', response.json())
        return response.json()

    def add_build(self, file, application_id=None, set_metadata=True, upload=True):
        '''Add a new build'''
        response = self.create_build(application_id)
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

        response = self.upload_build(build_id, file)
        if 'errorMessage' in response:
            LOGGER.debug('upload build failed, inform backend and then delete build')
            self.upload_build_failed(build_id, str(response))
            self.delete_build(build_id)
            return response

        response = self.upload_build_success(build_id, file)
        if 'errorMessage' in response:
            LOGGER.debug('upload build success call failed, delete build')
            self.delete_build(build_id)
        
        return response

    def add_build_without_app(self, file, set_metadata=True):
        return self.add_build(file, None, set_metadata, False)

    def delete_build(self, build_id):
        '''Delete a build'''
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        response = requests.delete(url, headers=self.headers)
        check_requests_response(response)
        LOGGER.debug('Delete build response: %s', response.json())
        return response.json()

    def delete_build_ticket(self, build_id, ticket_id):
        '''Delete a Zendesk ticket associated to a build'''
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['cmd'] = 'delete-ticket'
        params['ticket'] = ticket_id
        response = requests.patch(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Delete build ticket response: %s', response.json())
        return response.json()

    def get_build_ticket(self, build_id, ticket_id):
        '''Get the Zendesk ticket details'''
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['ticket'] = ticket_id

        response = requests.get(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Get build ticket response: %s', response.json())
        return response.json()

    def protect_start(self, build_id):
        '''Initiate build protection'''
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['cmd'] = 'protect'

        response = requests.patch(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Protect start response: %s', response.json())
        return response.json()

    def protect_get_status(self, build_id):
        '''Get the protection status of a build'''
        return self.list_builds(None, build_id)

    def protect_cancel(self, build_id):
        '''Cancel a protection job'''
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['cmd'] = 'cancel'

        response = requests.patch(url, headers=self.headers, params=params)
        check_requests_response(response)
        LOGGER.debug('Protect cancel response: %s', response.json())
        return response.json()

    def protect_download(self, build_id):
        '''Download a protected build file'''
        # Request a S3 presigned URL for the download
        url = '%s/%s' % (self.get_api_gw_url('builds'), build_id)

        params = {}
        params['url'] = 'protected'

        response = requests.get(url, headers=self.headers, params=params)
        check_requests_response(response)

        LOGGER.debug('Protect get download URL, response: %s', response.text)

        # Now download the protected binary.
        url = response.text
        local_filename = url.split('/')[-1]
        local_filename = local_filename.split('?')[0]
        print('Starting download of protected file')

        response = requests.get(url, stream=True)
        check_requests_response(response)
        LOGGER.debug('Download protection file response: %s', repr(response))
        with open(local_filename, 'wb') as file_handle:
            shutil.copyfileobj(response.raw, file_handle)
        print('Protected file downloaded to %s' % local_filename)

        result_file = open('protect_result.txt', 'w')
        result_file.write(local_filename)
        result_file.close()

        return None

    def add_build_to_application(self, build_id, application_id):
        '''Associate a build to an application'''
        url = '%s/%s/app' % (self.get_api_gw_url('builds'), build_id)

        body = {}
        body['applicationId'] = application_id

        response = requests.put(url, headers=self.headers, data=json.dumps(body))
        check_requests_response(response)
        LOGGER.debug('Add build to application response: %s', response.json())
        return response.json()

    def protect(self, file, options):
        '''High level protect command.
        This operation does the following
        - add_build
        - protect_start
        - poll protection state (protect_get_status) until protection is completed
        - protect_download'''

        # First add the build
        build = self.add_build_without_app(file, not options['skip_checks'])
        if 'errorMessage' in build:
            LOGGER.error('Failed to add new build %s', common.getSimpleErrorMessage(build['errorMessage']))
            return False

        if options['application_id'] == None:
            if options['skip_checks']:
                LOGGER.error('--application-id must be specified when skip-checks is used')
                return False
            applicationPackageId = build['applicationPackageId']
        else:
            applicationPackageId = options['application_id']
        os = get_os(file)

        applications = self.list_applications(None)
        application = None

        # Check if we have an app for this build (by searching for a matching
        # applicationPackageId)
        for app in applications:
            if app['applicationPackageId'] == applicationPackageId \
               and app['os'] == os:
                application = app
                break

        # If no application for the build exists then create a new app.
        # Take the applicationName from the package id and use default permissive permissions
        if not application:
            permissions = {}
            permissions['private'] = False
            permissions['no_upload'] = False
            permissions['no_delete'] = False

            application = self.add_application(applicationPackageId,
                                               applicationPackageId,
                                               os,
                                               permissions)
            if 'errorMessage' in application:
                print('Failed to add new application %s' % common.getSimpleErrorMessage(build['errorMessage']))
                return False

        self.add_build_to_application(build['id'], application['id'])

        # Upload the binary
        response = self.upload_build(build['id'], file)
        if 'errorMessage' in response:
            LOGGER.debug('upload build failed, inform backend and then delete build')
            LOGGER.warning(common.getSimpleErrorMessage(response['errorMessage']))
            self.upload_build_failed(build['id'], str(response))
            self.delete_build(build['id'])
            return False

        response = self.upload_build_success(build['id'], file)
        if 'errorMessage' in response:
            LOGGER.debug('upload build success call failed, delete build')
            LOGGER.warning(common.getSimpleErrorMessage(response['errorMessage']))
            self.delete_build(build['id'])
            return False

        # Start protection
        response = self.protect_start(build['id'])
        if 'errorMessage' in response:
            LOGGER.debug('protection start call failed, delete build')
            LOGGER.warning(common.getSimpleErrorMessage(response['errorMessage']))
            self.delete_build(build['id'])
            return False


        while True:
            build = self.protect_get_status(build['id'])

            if build['state'] not in PROTECT_STATES:
                print('Protection complete')
                break
            if build['state'] == 'protect_queue':
                print('In protect queue..')
            else:
                if 'progressData' in build:
                    print('Protecting', build['progressData']['progress'], '% complete')
            time.sleep(10)

        # Download the protected app on success.
        if build['state'] == 'protect_done':
            self.protect_download(build['id'])
            # This line is parsed by test-events-android to extract the build id. Do not change
            print('Protection succeeded with build id:%s' % build['id'])
        else:
            print('Protection failed with build id:%s' % build['id'])
            print('Turn on verbose logging (-v) for more details')


    def get_build_artifacts(self, build_id):
        '''Get build artifacts'''
        url = '%s/artifacts?buildId=%s' % (self.get_api_gw_url('report'), build_id)

        response = requests.get(url, headers=self.headers)
        check_requests_response(response)

        outdir = os.getcwd() + os.sep + build_id
        shutil.rmtree(outdir, ignore_errors=True)
        os.mkdir(outdir)

        artifact_urls = response.json()
        for url in artifact_urls:
            local_filename = url.split('/')[-1]
            local_filename = local_filename.split('?')[0]
            print('Downloading artifact %s' % local_filename)
            local_filename = outdir + os.sep + local_filename
            response = requests.get(url, stream=True)
            check_requests_response(response)
            with open(local_filename, 'wb') as file_handle:
                shutil.copyfileobj(response.raw, file_handle)
        print('Build artifacts downloaded to %s' % outdir)
        return None

    def get_statistics(self, start, end):
        '''Get APS statistics'''
        start_time = dateutil.parser.parse(start)
        if end:
            end_time = dateutil.parser.parse(end)
        else:
            end_time = datetime.now()

        params = {}

        url = '%s/statistics?start=%s&end=%s' % (self.get_api_gw_url('report'),
                                                 start_time, end_time)
        response = requests.get(url, headers=self.headers, params=params)
        check_requests_response(response)
        return response.json()

    def display_application_package_id(self, file):
        '''Extract the package id from the input file'''
        return extract_package_id(file)

    def set_protection_configuration(self, application_id, file):
        '''Set protection configuration for an application'''

        url = '%s/%s/protection-configuration' % (self.get_api_gw_url('applications'),
                                                  application_id)

        body = {}
        if file:
            with open(file, 'rb') as file_handle:
                body['configuration'] = json.load(file_handle)
        response = requests.put(url, headers=self.headers, data=json.dumps(body))
        check_requests_response(response)
        LOGGER.debug('Set protection configuration response: %s', response.json())
        return response.json()


    def set_signing_certificate(self, application_id, file):
        '''Set signing certificate for an application'''

        url = '%s/%s/signing-certificate' % (self.get_api_gw_url('applications'),
                                             application_id)

        body = {}
        if file:
            with open(file, 'r') as file_handle:
                body['certificate'] = file_handle.read()
        print(body)
        response = requests.put(url, headers=self.headers, data=json.dumps(body))
        check_requests_response(response)
        LOGGER.debug('Set signing certificate response: %s', response.json())
        return response.json()
