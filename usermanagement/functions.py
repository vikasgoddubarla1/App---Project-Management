
from django.http import HttpRequest
from .models import *
from .views import *
import random, string

#--------------------- generating unique recovery codes --------------------------------------------------------------------------

def generate_unique_recovery_codes(user, existing_codes, count=10):
   new_codes = []
   for _ in range(count):
       code = generate_unique_code(existing_codes)
       existing_codes.append(code)
       new_codes.append(code)

   return new_codes

#generating recovery code with length of 24 characters based on existing codes
def generate_unique_code(existing_codes, length=24):
   while True:
       code = generate_recovery_code(length)[0]
       if code not in existing_codes:
           return code

#generating recovery codes with length of 24 characters and 10 codes
def generate_recovery_code(length=24, count=10):
   codes = []
   for _ in range(count):
       code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
       code_parts = [code[i:i+12] for i in range(0, length, 12)]
       code = '-'.join(code_parts)
       codes.append(code)

   return codes

#------------------------------------------------------------------------------------------------------------------------------------------
def get_ip_address(request: HttpRequest) -> str:
    user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if user_ip_address:
        ip = user_ip_address.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_random_password(length=16):
   characters = string.ascii_letters + string.digits + string.punctuation
   random_string = ''.join(random.choice(characters) for _ in range(length))
   return random_string