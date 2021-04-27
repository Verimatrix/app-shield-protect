__all__ = ['common']


from js2py.pyjs import *
# setting scope
var = Scope( JS_BUILTINS )
set_global_object(var)

# Code follows:
var.registers(['getSimpleErrorMessage', 'getErrorMessage'])
@Js
def PyJsHoisted_getSimpleErrorMessage_(errorCode, this, arguments, var=var):
    var = Scope({'errorCode':errorCode, 'this':this, 'arguments':arguments}, var)
    var.registers(['errorMessage', 'errorCode'])
    var.put('errorMessage', var.get('getErrorMessage')(var.get('errorCode')))
    if var.get('errorMessage'):
        return var.get('errorMessage').get('message')
    else:
        return Js('NA')
PyJsHoisted_getSimpleErrorMessage_.func_name = 'getSimpleErrorMessage'
var.put('getSimpleErrorMessage', PyJsHoisted_getSimpleErrorMessage_)
@Js
def PyJsHoisted_getErrorMessage_(errorCode, this, arguments, var=var):
    var = Scope({'errorCode':errorCode, 'this':this, 'arguments':arguments}, var)
    var.registers(['errorCode'])
    while 1:
        SWITCHED = False
        CONDITION = (var.get('errorCode'))
        if SWITCHED or PyJsStrictEq(CONDITION, Js('FETCH_BUILDS_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Load Builds'),'message':Js('Failed to load builds list, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('CREATE_BUILD_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Add Build'),'message':Js('Could not add a new build, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('DELETE_APPLICATION_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Delete Application'),'message':Js('Could not delete application, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('DELETE_BUILD_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Delete Build'),'message':Js('Could not delete build, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('UPLOAD_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Upload Failed'),'message':Js('Network error while uploading application, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('UPLOAD_FAILED_BAD_FILENAME')):
            SWITCHED = True
            return Js({'title':Js('Upload Failed'),'message':Js('Please choose only a single file')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('MODIFY_APPLICATION_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Application Properties '),'message':Js('Failed to update application properties, please try again later')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('PROTECTION_START_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Protection Failed'),'message':Js('Failed to start protection, please try again later')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('DOWNLOAD_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Download Failed'),'message':Js('Failed to download the protected application, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('START_PROTECTION_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Start Protection'),'message':Js('Could not start the protection for this application.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_SIGNING_CERTIFICATE_MISSING')):
            SWITCHED = True
            return Js({'title':Js('Start Protection'),'message':Js("This application can't be protected without a signing certificate. Upload a signing certificate for this app in the application properties dialog.")})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_SIGNING_CERTIFICATE_INVALID')):
            SWITCHED = True
            return Js({'title':Js('Upload Certificate'),'message':Js('Please check that the input file is a valid X.509 certificate. The certificate must be PEM encoded and have sha256WithRSAEncryption Signature Algorithm.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_SIGNING_CERTIFICATE_UNSUPPORTED_ALGORITHM')):
            SWITCHED = True
            return Js({'title':Js('Upload Certificate'),'message':Js('The Signing certificate has an unsupported algorithm. The certificate must have sha256WithRSAEncryption Signature Algorithm.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_SIGNING_CERTIFICATE_UNSUPPORTED_SDK')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('The uploaded app minSdkVersion is not supported for the signature algorithm. The signing certificate bound integrity verification feature is supported only for applications with minSdkVersion between 21 and 23.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ABORT_PROTECTION_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Abort Protection'),'message':Js('Could not abort protection for this application.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ARCHIVE_CREATION_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Upload Build'),'message':Js('Failed to create directory archive, please upload an Xcode Archive file')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_MALFORMED_UPLOAD_FILENAME')):
            SWITCHED = True
            pass
        if SWITCHED or PyJsStrictEq(CONDITION, Js('INVALID_FILES')):
            SWITCHED = True
            return Js({'title':Js('Upload Build'),'message':Js('Wrong file type selected, please upload an APK file, or an Xcode Archive file or directory.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_NO_FILES')):
            SWITCHED = True
            return Js({'title':Js('Upload Build'),'message':Js('Please select at least one file for upload')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_UPLOAD_ALREADY_ACTIVE')):
            SWITCHED = True
            return Js({'title':Js('Upload Active'),'message':Js('Please wait for the current upload to complete')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('FAILED_PROTECTION_START')):
            SWITCHED = True
            return Js({'title':Js('Application Protection'),'message':Js('Failed to start protection, please try again later')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('CREATE_APPLICATION_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Create Application'),'message':Js('Could not create an application at this time, please try again later')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('FETCH_APPLICATIONS_FAILED')):
            SWITCHED = True
            return Js({'title':Js('Fetch Applications'),'message':Js('Could not load applications, please try again later.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('INVALID_CLAIMS')):
            SWITCHED = True
            return Js({'title':Js('Fetch Applications'),'message':Js('APS is not enabled for the current user.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('MINIMUM_SDK_VERSION_ANDROID_TOO_SMALL')):
            SWITCHED = True
            return Js({'title':Js('Upload failed'),'message':Js('The minimum SDK version for this APK is too low.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ANDROID_PERMISSION_INTERNET_MISSING')):
            SWITCHED = True
            return Js({'title':Js('Upload failed'),'message':Js('The Android permission INTERNET is missing in this APK.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_APPLICATION_NOT_VALID')):
            SWITCHED = True
            return Js({'title':Js('Create application'),'message':Js('Application name is not valid.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_APPLICATION_EXISTS')):
            SWITCHED = True
            return Js({'title':Js('Create application'),'message':Js('An application with that name already exists, please use a different name.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('BUILD_AND_APPLICATION_PACKAGE_IDS_MISMATCHING')):
            SWITCHED = True
            return Js({'title':Js('Create application'),'message':Js('The file can not be added to this application, please choose a different application or create a new application.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('BUILD_AND_SELECTED_APPLICATION_PACKAGE_IDS_MISMATCHING')):
            SWITCHED = True
            return Js({'title':Js('Create application'),'message':Js('The uploaded file does not match the selected application. Create a new application below or upload a different file.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ANDROID_APPLICATION_DEBUGGABLE')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('Debuggable applications can not be protected.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ANDROID_MINIMUM_SDK_VERSION_TOO_SMALL')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('The android minimum SDK version for this application is too low.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ANDROID_MINIMUM_SDK_VERSION_MISSING')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('Minimum Android SDK version for this application is not specified.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ANDROID_MINIMUM_SDK_VERSION_TOO_BIG')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('The android minimum SDK version for this application is too large.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ANDROID_TARGET_SDK_VERSION_TOO_BIG')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('The android target SDK version for this application is too large.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('IOS_XCODE_VERSION_UNSUPPORTED')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('The XCode version used to build this application is not supported.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('BUILD_OS_NOT_VALID')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('Application OS is not valid.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_INVALID_FILENAME')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('Invalid file name. File name can contain alphanumeric characters, spaces, dots, underscores and hyphens.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_UPLOAD_LIMIT_EXCEEDED')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('Number of allowed uploads per month exceeded. Please upgrade your account to enable additional uploads.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_APPLICATION_LIMIT_EXCEEDED')):
            SWITCHED = True
            return Js({'title':Js('Create Application'),'message':Js('Number of allowed apps exceeded. Please upgrade your subscription, or alternatively delete one or more existing apps.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_STORAGE_LIMIT_EXCEEDED')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js('Storage limits exceeded. Please upgrade your account to create additional storage, or alternatively delete one or more builds to free storage.')})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_PERMISSION_APPLICATION_UPLOAD')):
            SWITCHED = True
            return Js({'title':Js('Upload Application'),'message':Js("You don't have permission to upload new builds to this application.")})
        if SWITCHED or PyJsStrictEq(CONDITION, Js('ERROR_PERMISSION_APPLICATION_MODIFY')):
            SWITCHED = True
            return Js({'title':Js('Application Properties'),'message':Js("You don't have permission to modify this application.")})
        SWITCHED = True
        break
PyJsHoisted_getErrorMessage_.func_name = 'getErrorMessage'
var.put('getErrorMessage', PyJsHoisted_getErrorMessage_)
pass
pass
pass


# Add lib to the module scope
common = var.to_python()