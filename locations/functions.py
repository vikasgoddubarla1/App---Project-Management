import random, string
def generate_location_code(length=16):
   characters = string.ascii_letters + string.digits
   random_string = ''.join(random.choice(characters) for _ in range(length))
   return random_string

def generate_location_micropage_id(length=26):
   characters = string.ascii_uppercase + string.digits
   lengths = [9, 4, 4, 9]
   length_string = [''.join(random.choice(characters) for _ in range(length)) for length in lengths]
   random_string = '-'.join(length_string)
   return random_string