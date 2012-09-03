import requests

from auspost import common


DEV_ENDPOINT = 'https://devcentre.auspost.com.au/myapi'
PRD_ENDPOINT = 'https://api.auspost.com.au'


def api_request(f):
    def func(*args, **kwargs):
        s = "".join([s.capitalize() for s in f.__name__.split('_')])
        kwargs['api_name'] = s
        return f(*args, **kwargs)
    return func


class DeliveryChoiceApi(common.AuspostObject):

    DELIVERY_NETWORKS = {
        '01': 'Standard',
        '02': 'Express',
    }

    def __init__(self, username=None, password=None):
        self.url = DEV_ENDPOINT
        self.username = 'anonymous@auspost.com.au'
        self.password = 'password'
        self.format = 'json' 

        if username and password:
            self.url = PRD_ENDPOINT
            self.username = username
            self.password = password

    @api_request
    def delivery_dates(self, from_postcode, to_postcode, lodgement_date,
                       network_id='01', number_of_dates=1, **kwargs):

        response =  self.send_request(kwargs.get('api_name'), params={
            'fromPostcode': from_postcode,
            'toPostcode': to_postcode,
            'lodgementDate': lodgement_date,
            'networkId': network_id,
            'numberOfDates': number_of_dates,
        })
        return DeliveryDate.from_json(response.json)

    @api_request
    def delivery_timeslots(self, day=None, **kwargs):
        """ valid values 1-7 (Mon - Sun) or nothing (returns all) """
        raise NotImplementedError()

    @api_request
    def postcode_capability(self, postcode=None, **kwargs):
        """ valid postcode or nothing (returns all postcodes) """
        raise NotImplementedError()
        #response =  self.send_request(kwargs.get('api_name'), {'postcode': postcode})

    @api_request
    def customer_collection_points(self, state=None, postcode=None,
                                   last_update=None, **kwargs):
        raise NotImplementedError()

    @api_request
    def query_tracking(self, tracking_id, **kwargs):
        #TODO Check for list first and convert sting to list of one item
        raise NotImplementedError()

    @api_request
    def validate_address(self, line1, suburb, state, postcode, line2=None,
                         country="Australia", **kwargs):
        raise NotImplementedError()

    def get_parameter_kwargs(self, **kwargs):
        params = {}
        for key, value in kwargs:
            parts = key.split("_")
            key = "".join(parts[:1]+[k.capitalize() for k in parts[1:]])
            params[key] = value
        return params

    def send_request(self, path, params, **kwargs):
        request_url = u"%s/%s.%s" % (self.url, path, self.format)
        response = requests.get(
            request_url,
            auth=(self.username, self.password),
            cookies={'OBBasicAuth': 'fromDialog'},
            params=params,
        )
        #TODO handle HTTP errors
        self.check_response(response)
        return response

    def check_response(self, response):
        try:
            exc = response.json.values()[0]['BusinessException']
            code, message = exc['Code'], exc['Description']
        except:
            return

        if code:
            raise common.AusPostException(code, message)


class DeliveryDate(common.AuspostObject):

    def __init__(self, delivery_date, working_days, timed_delivery):
        self.delivery_date = delivery_date
        self.working_days = working_days
        self.timed_delivery = timed_delivery

    @classmethod
    def from_json(cls, json):
        try:
            res = json['DeliveryEstimateRequestResponse']['DeliveryEstimateDates']
            res = res['DeliveryEstimateDate']
        except KeyError:
            raise Exception
    
        res = cls._ensure_list(res)

        dates = []
        for item in res:
            dates.append(cls(
                common.get_aware_utc_datetime(item['DeliveryDate']),
                item['NumberOfWorkingDays'],
                item['TimedDeliveryEnabled'],
            ))

        return dates

    def __repr__(self):
        return "<%s date='%s' working_days='%s'>" % (
            self.__class__.__name__,
            self.delivery_date,
            self.working_days,
        )

    def __unicode__(self):
        return "%s %s" % (self.delivery_date, self.timed_delivery)


class TimePeriod(common.AuspostObject):

    def __init__(self, start_time, end_time, duration):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration

    @classmethod
    def from_json(cls, json):
        periods = []
        for item in json:
            start_time = item['StartTime'].split(':')
            end_time = item['EndTime'].split(':')

            name = item['TimePeriodName']
            sh, eh = int(start_time[0]), int(end_time[0])
            if name == "PM":
                if sh > 12:
                    sh = sh + 12
                if eh > 12:
                    eh = eh + 12
            else:
                if sh == 12:
                    sh = 0
                if eh == 12:
                    eh = 0

            periods.append(cls(
                start_time= ":".join([str(sh)]+start_time[1:]),
                end_time= ":".join([str(eh)]+end_time[1:]),
                duration=item['Duration'],
            ))
        return periods


class TimeSlot(common.AuspostObject):

    def __init__(self, week_day, periods=None):
        self.day = week_day
        self.periods = periods or []

    @classmethod
    def from_json(cls, json):
        try:
            result = json['DeliveryTimeslots']['DayTimeslot']
        except KeyError:
            raise Exception

        timeslots = []
        for item in result:
            periods = TimePeriod.from_json(item['TimePeriod'])
            timeslots.append(cls(
                item['WeekdayDescription'],
                periods,
            ))
        return timeslots


class PostcodeDeliveryCapability(common.AuspostObject):

    def __init__(self, postcode, days, last_modified):
        self.postcode = postcode
        self.days = days
        self.last_modified = last_modified

    @classmethod
    def from_json(cls, json):
        try:
            result = json['PostcodeDeliveryCapabilities']
            result = result['PostcodeDeliveryCapability']
        except:
            raise Exception

        result = cls._ensure_list(result)

        capabilities = []
        for item in result:
            utc_dt = common.get_aware_utc_datetime(item['LastModified'])
            capabilities.append(
                cls(
                    postcode=item['Postcode'],
                    last_modified=utc_dt,
                    days=Day.from_json(item['WeekDay']), 
                )
            )
        return capabilities


class Day(common.AuspostObject):

    def __init__(self, name, standard_delivery_enabled, timed_delivery_enabled):
        self.name = name 
        self.standard_delivery_enabled = standard_delivery_enabled
        self.timed_delivery_enabled = timed_delivery_enabled

    @classmethod
    def from_json(cls, json):
        days = []
        for item in json:
            days.append(
                cls(
                    name=common.DAY_CODES[item['DayType']],
                    standard_delivery_enabled=item['StandardDeliveryEnabled'],
                    timed_delivery_enabled=item['TimedDeliveryEnabled'],
                )
            )
        return days
