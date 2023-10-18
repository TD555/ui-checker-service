import re

def get_image_byte_data(image_data):
    if 'data:image/png;base64,' in str(image_data):
        match = re.match(r'(data:image/png;base64,)(.*)', str(image_data))
    elif 'data:image/jpg;base64,' in str(image_data):
        match = re.match(r'(data:image/jpn;base64,)(.*)', str(image_data))
    elif 'data:image/jpeg;base64' in str(image_data):
        match = re.match(r'(data:image/jpeg;base64,)(.*)', str(image_data))
    else: return image_data.decode()

    return match.groups()[1]


def base_size(b64string):
    return (len(b64string) * 3) / 4 - b64string.count('=', -2)
