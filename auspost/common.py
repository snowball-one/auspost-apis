import pytz

from dateutil.tz import tzoffset
from dateutil import parser as date_parser


DELIVERY_CHOICE_ERROR_CODES = {
    # delivery date
    1001: "Invalid from postcode",
    1002: "Invalid to postcode",
    1003: "Invalid network id",
    1004: "Invalid lodgement date",
    1005: "Invalid number of dates",
    # timeslots
    1101: "Invalid day",
    # post code capabilities
    1201: "Invalid postcode",
    1202: "No postcode capability found",
    # customer collection points
    1301: "Invalid state",
    1302: "Invalid postcode",
    1303: "Invalid date",
    # query tracking
    1401: "Invalid tracking ID",
    1402: "Maximum of 10 tracking IDs is allowed",
    1403: "A tracking ID is invalid or exeeds 50 characters",
    1404: "Product is not trackable",
    # validate address
    1501: "Invalid address line",
    1502: "Invalid suburb",
    1503: "Invalid state",
    1504: "Invalid postcode",
    1505: "Invalid country",
}

DAY_CODES = {
    1: 'Monday',
    2: 'Tuesday',
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday',
    7: 'Sunday',
}


class AusPostException(Exception):

    def __init__(self, code, msg=None):
        self.code = code

        if not msg:
            msg = DELIVERY_CHOICE_ERROR_CODES.get(code, '')

        self.message = msg
        super(AusPostException, self).__init__(self.get_error_message())

    def get_error_message(self):
        return u"Error %d: %s" % (self.code, self.message)


class AusPostHttpException(AusPostException):
    pass


def get_aware_utc_datetime(datetime_str):
    dt = date_parser.parse(datetime_str)
    if dt.tzinfo:
        dt = dt.astimezone(tzoffset(None, 0))
        utc_dt = pytz.utc.normalize(dt)
    else:
        utc_dt = pytz.utc.localize(dt)
    return utc_dt


def is_valid_postcode(postcode):
    try:
        return bool(int(postcode) > 999)
    except ValueError:
        return False


def ensure_list(json):
    """
    Ensure that the *json* passed in is a list and not just a simple
    dictionary. If a dictionary is passed in a list of a single item
    will be returned otherwise, *json* is returned unchanged.

    This is required because the generated JSON from the APIs will
    return a dictionary for items such as ``Article`` with only a single
    item present instead of a list with one item. Calling this method
    prevents prevents unneccessary checking and exception handling.
    """
    try:
        json.keys()    # if this is a dictionary
        return [json]  # return it as a list
    except AttributeError:
        return json
