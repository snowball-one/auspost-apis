import requests


PRD_ENDPOINT = 'https://devcentre.auspost.com.au/myapi/'
DEV_ENDPOINT = 'https://api.auspost.com.au/'


class DeliveryChoiceApi(object):

    def __init__(self, username=None, password=None, response_format='json'):
        self.url = DEV_ENDPOINT
        self.username = 'anonymous@auspost.com.au'
        self.password = 'password'
        self.format = response_format

        if username and password:
            self.url = PRD_ENDPOINT
            self.username = username
            self.password = password
