from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.exceptions import APIException
class PermissionDenied(PermissionDenied):
    status_code = status.HTTP_421_MISDIRECTED_REQUEST
    default_detail = "You do not have permission to perform this action."
    default_code = 'permission_denied'
    



