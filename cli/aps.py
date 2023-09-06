#!/usr/bin/python
'''Entrypoint for APS CLI'''
import argparse
import json
import logging
import os
import sys
import traceback

import coloredlogs

from aps_commands import ApsCommands
from aps_utils import get_config, authenticate_secret

LOGGER = logging.getLogger(__name__)

# set environment variables that control coloredlog module output
os.environ['COLOREDLOGS_LOG_FORMAT'] = '%(levelname)s:%(message)s'
os.environ['COLOREDLOGS_FIELD_STYLES'] = ''
os.environ['COLOREDLOGS_LEVEL_STYLES'] = 'debug=blue;info=green;warning=yellow;' +\
                                      'error=red,bold'

def supported_commands():
    '''Returns the list of supported commands'''
    return ['protect',
            'list-applications',
            'add-application',
            'update-application',
            'delete-application',
            'set-signing-certificate',
            'list-builds',
            'add-build',
            'delete-build',
            'protect-start',
            'protect-get-status',
            'protect-cancel',
            'protect-download',
            'get-account-info',
            'display-application-package-id' ]

class Aps:
    '''Class encapsulating all supported command line options'''
    def __init__(self):
        self.commands = None

        parser = argparse.ArgumentParser(
            description='APS command line tool',
            usage='''aps [global-options] <command> [<command-options>]
    The following commands are available

      * protect

      * list-applications
      * add-application
      * update-application
      * delete-application
      * set-signing-certificate

      * list-builds
      * add-build
      * delete-build

      * protect-start
      * protect-get-status
      * protect-cancel
      * protect-download

      * get-account-info
      * display-application-package-id

    Use aps <command> -h for information on a specific command.
    Use aps -h for information on the global options.
     ''')

        parser.add_argument('command', help='Command to run')

        parser.add_argument('-v',
                            action='store_true',
                            help='Verbose debug output')

        parser.add_argument('-c', '--client-id', type=str, help='App Shield API Key ID. Key must have Protection scope.')
        parser.add_argument('-s', '--client-secret', type=str, help='App Shielid API Key secret.')
        parser.add_argument('--api-gateway-url', type=str, required=False, help = 'Optional Api gateway URL')
        parser.add_argument('--access-token-url', type=str, required=False, help='Optional Access token URL')

        # find the index of the command argument
        self.command_pos = len(sys.argv)
        i = 0
        for arg in sys.argv[1:]:
            i += 1
            if arg in supported_commands():
                self.command_pos = i + 1
                break

        # parse_args defaults to [1:] for args, but we exclude the command arguments
        # Defer parsing and validation of the global args (parse_global_args method) 
        # until we have parsed the command arguments. Otherwise this would prevent
        # running aps.py COMMAND -h to get help on the COMMAND arguments unless
        # all mandatory global args were to be supplied.
        args = parser.parse_args(sys.argv[1:self.command_pos])

        # python doesn't allow for hyphens in method names
        mapped_command = args.command.replace('-', '_')

        if not hasattr(self, mapped_command):
            print('Unrecognized command')
            parser.print_help()
            sys.exit(1)

        # invoke command
        try:
            response = getattr(self, mapped_command)(args)
            if response is not None:
                if isinstance(response, str):
                    print(response)
                else:
                    print(json.dumps(response, indent=2, sort_keys=True))
        except Exception as e:
            traceback.print_exc()
            sys.exit(1)

    def parse_global_args(self, args):
        if args.v:
            coloredlogs.install(level=logging.DEBUG)
        else:
            coloredlogs.install(level=logging.ERROR)

        config = get_config(args)

        if args.client_id and args.client_secret:
            headers = authenticate_secret(args.client_id, args.client_secret, config)
            using_client_secret = True
        else:
            msg = ('Error: missing authentication credentials.\n'
                   'A --client-id, --client-secret pair of arguments must be provided')
            LOGGER.error(msg)
            sys.exit(1)

        openapi_file = os.path.abspath(os.path.join(os.pardir, os.pardir, 'versions', 'openapi.txt'))
        if os.path.exists(openapi_file):
            with open(openapi_file, 'r') as file:
                version = file.read().replace('\n', '')
                headers['Accept'] = 'application/vnd.aps.appshield.verimatrixcloud.net;version=%s' % version

        self.commands = ApsCommands(headers, config, using_client_secret, 0)


    def protect(self, global_args):
        '''Perform APS protection from an input file.

        This is a high level command that takes an input
        binary to be protected, performs protection and outputs the protected 
        binary. This command may take many minutes to complete.'''

        parser = argparse.ArgumentParser(
            usage='aps protect [<args>]',
            description='Perform APS protection on the input file.')

        parser.add_argument('--file', type=str, required=True,
                            help='Build file (aab, apk or zipped xcarchive folder)')
        parser.add_argument('--skip-checks', help='Skip pre-upload checks on the app.', action='store_true', default=False)
        parser.add_argument('--application-id', type=str, required=False, 
                            help='''Application ID. This identifies the application being protected.
                            If --skip-checks is used this argument is mandatory''')

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])
        options = {}
        options['skip_checks'] = args.skip_checks
        options['application_id'] = args.application_id

        self.parse_global_args(global_args)

        return self.commands.protect(args.file, options)

    def get_account_info(self, global_args):
        '''Get info about the user and organization'''
        parser = argparse.ArgumentParser(
            usage='aps get-account-info [<args>]',
            description='Returns information about the user and organization (customer)')

        parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.get_account_info()

    def add_application(self, global_args):
        '''Add a new application'''
        parser = argparse.ArgumentParser(
            usage='aps add-application [<args>]',
            description='''Add a new application. By default the application is
            accessible to other users within your organization. The --private, --no-upload,
            --no-delete options can be used to restrict access to the application.
            ''')
        parser.add_argument('--os', type=str, required=True,
                            choices=['ios', 'android'], help='Operating System.')
        parser.add_argument('--name', type=str, required=True, help='Friendly name for application.')
        parser.add_argument('--package-id', type=str, required=True, help='Application package ID.')
        parser.add_argument('--group', type=str, required=False, help='Optional group identifier.')
        parser.add_argument('--private',
                            help='''Prevent the application from being visible to other users.
                            This option will automatically set each of --no-upload
                            and --no-delete options.''',
                            action='store_true', default=False)
        parser.add_argument('--no-upload',
                            help='Prevent other users from uploading new builds for this app.',
                            action='store_true', default=False)
        parser.add_argument('--no-delete',
                            help='Prevent other users from deleting builds for this app.',
                            action='store_true', default=False)

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])
        permissions = {}
        permissions['private'] = args.private
        permissions['no_upload'] = args.no_upload
        permissions['no_delete'] = args.no_delete

        self.parse_global_args(global_args)
        return self.commands.add_application(args.name, args.package_id, args.os, permissions, args.group)

    def update_application(self, global_args):
        '''Update application properties'''
        parser = argparse.ArgumentParser(
            usage='aps update-application [<args>]',
            description='''Update application properties. The application name and 
            permission related properties can be modified''')
        parser.add_argument('--application-id', type=str, required=True, 
                            help='''Application ID. This identifies the application whose 
                            properties should be updated, this property cannot itself be 
                            changed. The remaining arguments correspond to application 
                            properties that can be updated by this call.''')
        parser.add_argument('--name', type=str, required=True, help='Friendly name for application')
        parser.add_argument('--private',
                            help='''Prevent the app from being visible to other users. This option
                            will automatically set each of the --no-upload
                            and --no-delete options.''',
                            action='store_true', default=False)
        parser.add_argument('--no-upload',
                            help='Prevent other users from uploading new builds for this app.',
                            action='store_true', default=False)
        parser.add_argument('--no-delete',
                            help='Prevent other users from deleting builds for this app.',
                            action='store_true', default=False)

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])
        permissions = {}
        permissions['private'] = args.private
        permissions['no_upload'] = args.no_upload
        permissions['no_delete'] = args.no_delete

        self.parse_global_args(global_args)
        return self.commands.update_application(args.application_id, args.name, permissions)

    def list_applications(self, global_args):
        '''List applications'''
        parser = argparse.ArgumentParser(
            usage='aps list-applications [<args>]',
            description='''List applications.
            Optional "application-id" or "group" parameters can be specified to restrict 
            the list of applications that are reported by this call.
            
            When the "application-id" parameter is provided this operation returns the
            specific application identified by "application-id".

            When the "group" parameter is provided this operation returns all
            applications belonging to the specified group.
            
            When neither "application-id" or "group" are provided this operation returns the 
            list of all applications.''')
        parser.add_argument('--application-id', type=str, required=False, help='Application ID')
        parser.add_argument('--group', type=str, required=False, help='Application group identifier')

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.list_applications(args.application_id, args.group)

    def delete_application(self, global_args):
        '''Delete an application'''
        parser = argparse.ArgumentParser(
            usage='aps delete-application [<args>]',
            description='''Delete application. This operation will also delete all builds
            belonging to this application.''')
        parser.add_argument('--application-id', type=str, required=True, help='Application ID')

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.delete_application(args.application_id)

    def list_builds(self, global_args):
        '''List builds'''
        parser = argparse.ArgumentParser(
            usage='aps list-builds [<args>]',
            description='''List builds.
            
            Optional "application-id" or "build-id" parameters can be specified to restrict 
            the list of builds that are reported by this call.
            
            When the "application-id" parameter is provided this operation returns the list 
            of builds for that particular application. When the "build-id" parameter is 
            provided this operation returns the specific build identified by "build-id".
            
            When neither "application-id" or "build-id" are provided this operation returns 
            all builds.''')

        parser.add_argument('--application-id', type=str, required=False, help='Application ID')
        parser.add_argument('--build-id', type=str, required=False, help='Build ID')

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.list_builds(args.application_id, args.build_id)

    def add_build(self, global_args):
        '''Add a new build'''
        parser = argparse.ArgumentParser(
            usage='aps add-build [<args>]',
            description='Add a new build')

        parser.add_argument('--application-id', type=str, required=True, help='Application ID')
        parser.add_argument('--file', type=str, required=False,
                            help='Build file (apk or xcarchive folder)')
        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.add_build(args.file, args.application_id)

    def delete_build(self, global_args):
        '''Delete a build'''
        parser = argparse.ArgumentParser(
            usage='aps delete-build [<args>]',
            description='Delete build')
        parser.add_argument('--build-id', type=str, required=True, help='Build ID')

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.delete_build(args.build_id)

    def protect_start(self, global_args):
        '''Start build protection'''
        parser = argparse.ArgumentParser(
            usage='aps protect-start [<args>]',
            description='Initiate protection of a previously added build')

        parser.add_argument('--build-id', type=str, required=True, help='Build ID')
        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.protect_start(args.build_id)

    def protect_cancel(self, global_args):
        '''Cancel protection of a build'''
        parser = argparse.ArgumentParser(
            usage='aps protect-cancel [<args>]',
            description='Cancel protection of a build.')

        parser.add_argument('--build-id', type=str, required=True, help='Build ID')
        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.protect_cancel(args.build_id)

    def protect_get_status(self, global_args):
        '''Get the status of a build'''
        parser = argparse.ArgumentParser(
            usage='aps protect-get-status [<args>]',
            description='''Get the status of a build. This includes progress
            information when a protection build is ongoing.''')

        parser.add_argument('--build-id', type=str, required=True, help='Build ID')
        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.protect_get_status(args.build_id)

    def protect_download(self, global_args):
        '''Download a protected build'''
        parser = argparse.ArgumentParser(
            usage='aps protect-download [<args>]',
            description='Download a previously protected build.')

        parser.add_argument('--build-id', type=str, required=True, help='Build ID')
        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.protect_download(args.build_id)

    def display_application_package_id(self, global_args):
        '''Utility to extract and display the application package id from a file.'''
        parser = argparse.ArgumentParser(
            usage='aps display_application_package_id [<args>]',
            description='''Display the application package id for a input file.
            This can be used as input when calling add-application. 
            ''')

        parser.add_argument('--file', type=str, required=True,
                            help='Input file (apk or xcarchive folder)')
        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.display_application_package_id(args.file)

    def set_signing_certificate(self, global_args):
        '''Set signing certificate'''
        parser = argparse.ArgumentParser(
            usage='aps set-signing-certificate [<args>]',
            description='''Set signing certificate for an application.''')
        parser.add_argument('--application-id', type=str, required=True, help='Application ID')
        parser.add_argument('--file', type=str, required=False,
                            help='PEM encoded certificate file. If omitted then this unsets any previously set certificate')

        # inside subcommands ignore the first command_pos argv's
        args = parser.parse_args(sys.argv[self.command_pos:])

        self.parse_global_args(global_args)
        return self.commands.set_signing_certificate(args.application_id, args.file)

if __name__ == '__main__':
    Aps()
