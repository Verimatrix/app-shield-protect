# Copyright (c) 2019 - 2021. Verimatrix. All Rights Reserved.
# All information in this file is Verimatrix Confidential and Proprietary.
'''APS Exceptions'''


class ApsException(Exception):
    """APS Generic Exception."""

class ApsHttpException(ApsException):
    """A HTTP error occurred."""
