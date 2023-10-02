# Copyright (c) 2019 - 2021. Verimatrix. All Rights Reserved.
# All information in this file is Verimatrix Confidential and Proprietary.

import requests
import backoff


def check_requests_response(response):
    '''Check response from requests call. If there is an error message coming from
    APS backend then return it, otherwise raise an exception'''
    if 'Content-Type' in response.headers and \
        response.headers['Content-Type'] == 'application/json':
        if 'errorMessage' in response.json():
            return
    response.raise_for_status()


@backoff.on_exception(wait_gen=backoff.expo,
                      exception=requests.exceptions.RequestException,
                      max_tries=6,
                      max_time=30)
def request_with_retry(method, url, **kwargs):
    '''Requests with retry'''
    response = requests.request(method, url, **kwargs)
    check_requests_response(response)
    return response

class ApsRequest:
    @staticmethod
    def get(url, **kwargs):
         return request_with_retry('get', url, **kwargs)

    @staticmethod
    def put(url, **kwargs):
         return request_with_retry('put', url, **kwargs)

    @staticmethod
    def post(url, **kwargs):
         return request_with_retry('post', url, **kwargs)

    @staticmethod
    def patch(url, **kwargs):
         return request_with_retry('patch', url, **kwargs)

    @staticmethod
    def delete(url, **kwargs):
         return request_with_retry('delete', url, **kwargs)

    @staticmethod
    def get(url, **kwargs):
         return request_with_retry('get', url, **kwargs)
