import random
import string

def format_date(da, ds):
    return da.strftime('%d %B %Y'), ds.strftime('%d %B %Y')


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))
