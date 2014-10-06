import requests

from datetime import date

from auspost import common


DEV_ENDPOINT = 'https://devcentre.auspost.com.au/myapi'
PRD_ENDPOINT = 'https://api.auspost.com.au'


def api_request(f):
    def func(*args, **kwargs):
        s = "".join([s.capitalize() for s in f.__name__.split('_')])
        kwargs['api_name'] = s
        return f(*args, **kwargs)
    return func


class DeliveryChoiceApi(object):

    DELIVERY_NETWORKS = {
        '01': 'Standard',
        '02': 'Express'}

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

        if not common.is_valid_postcode(from_postcode):
            raise common.AusPostException(1001)

        if not common.is_valid_postcode(to_postcode):
            raise common.AusPostException(1002)

        if network_id not in self.DELIVERY_NETWORKS:
            raise common.AusPostException(1003)

        if lodgement_date < date.today():
            raise common.AusPostException(1004)

        if number_of_dates not in range(1, 11):
            raise common.AusPostException(1005)

        response = self.send_request(kwargs.get('api_name'), params={
            'fromPostcode': from_postcode,
            'toPostcode': to_postcode,
            'lodgementDate': lodgement_date.strftime("%Y-%m-%d"),
            'networkId': network_id,
            'numberOfDates': number_of_dates})
        return DeliveryDate.from_json(response.json())

    @api_request
    def delivery_timeslots(self, day=None, **kwargs):
        """ valid values 1-7 (Mon - Sun) or nothing (returns all) """
        raise NotImplementedError()

    @api_request
    def postcode_capability(self, postcode=None, **kwargs):
        """ valid postcode or nothing (returns all postcodes) """
        raise NotImplementedError()

    @api_request
    def customer_collection_points(self, state=None, postcode=None,
                                   last_update=None, **kwargs):
        raise NotImplementedError()

    @api_request
    def query_tracking(self, tracking_numbers, **kwargs):
        response = self.send_request(
            kwargs.get('api_name'),
            params={'q': ",".join(tracking_numbers)})
        return TrackingResult.from_json(response.json())

    @api_request
    def validate_address(self, line1, suburb, state, postcode, line2=None,
                         country="Australia", **kwargs):
        response = self.send_request(kwargs.get('api_name'), params={
            "addressLine1": line1,
            "addressLine2": line2,
            "suburb": suburb,
            "state": state,
            "postcode": postcode,
            "country": country})
        return ValidationResult.from_json(response.json())

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
            params=params)
        self.check_response(response)
        return response

    def check_response(self, response):
        if response.status_code != 200:
            raise common.AusPostHttpException(
                response.status_code, response.reason)

        try:
            exc = response.json().values()[0]['BusinessException']
            code, message = exc['Code'], exc['Description']
        except:
            return

        if code:
            raise common.AusPostException(code, message)


class DeliveryDate(object):

    def __init__(self, delivery_date, working_days, timed_delivery):
        self.delivery_date = delivery_date
        self.working_days = working_days
        self.timed_delivery = timed_delivery

    @classmethod
    def from_json(cls, json):
        try:
            res = json['DeliveryEstimateRequestResponse'][
                'DeliveryEstimateDates']
            res = res['DeliveryEstimateDate']
        except KeyError:
            raise Exception

        res = common.ensure_list(res)

        dates = []
        for item in res:
            dates.append(cls(
                common.get_aware_utc_datetime(item['DeliveryDate']),
                item['NumberOfWorkingDays'],
                item['TimedDeliveryEnabled']))

        return dates

    def __repr__(self):
        return "<%s date='%s' working_days='%s'>" % (
            self.__class__.__name__, self.delivery_date, self.working_days)

    def __unicode__(self):
        return "%s %s" % (self.delivery_date, self.timed_delivery)


class TimePeriod(object):

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
                start_time=":".join([str(sh)]+start_time[1:]),
                end_time=":".join([str(eh)]+end_time[1:]),
                duration=item['Duration']))
        return periods


class TimeSlot(object):

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
            timeslots.append(cls(item['WeekdayDescription'], periods))
        return timeslots


class PostcodeDeliveryCapability(object):

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

        result = common.ensure_list(result)

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


class Day(object):

    def __init__(self, name, standard_delivery_enabled,
                 timed_delivery_enabled):
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


class TrackingResult(object):

    def __init__(self, id, article=None, consignment=None):
        self.id = unicode(id)
        self.article = article
        self.consignment = consignment

    @classmethod
    def from_json(cls, json):
        tracking_results = []
        try:
            tracking_list = json['QueryTrackEventsResponse']['TrackingResult']
        except KeyError:
            raise Exception

        for item in common.ensure_list(tracking_list):
            tracking_result = cls(id=item['TrackingID'])

            articles = Article.from_json(item.get('ArticleDetails', []))
            if len(articles) == 1:
                tracking_result.article = articles[0]
            else:
                raise common.AusPostException(
                    'found more than 1 article in JSON response')

            if 'ConsignmentDetails' in item:
                consignment = Consignment.from_json(item['ConsignmentDetails'])
                tracking_result.consignment = consignment

            tracking_results.append(tracking_result)

        return tracking_results


class ValidationResult(object):

    def __init__(self, address, is_valid=False):
        self.address = address
        self.is_valid = is_valid

    @property
    def has_address(self):
        return self.address is not None

    @classmethod
    def from_json(cls, json):
        try:
            is_valid = json['ValidateAustralianAddressResponse'][
                'ValidAustralianAddress']
        except KeyError:
            raise Exception

        try:
            address = Address.from_json(
                json['ValidateAustralianAddressResponse']['Address'])
        except KeyError:
            address = None

        return cls(address=address, is_valid=is_valid)

    def __unicode__(self):
        return "{address} is {valid}".format(
            address=unicode(self.address),
            valid='valid' if self.is_valid else 'invalid')


class Article(object):

    def __init__(self, id, product_name=None, event_notification=None,
                 status=None, origin=None, destination=None, events=None):
        self.id = unicode(id)
        self.event_notification = event_notification
        self.product_name = product_name
        self.status = status
        self.origin = origin
        self.destination = destination
        self.events = events or []

    @classmethod
    def from_json(cls, json):
        articles = []

        for item in common.ensure_list(json):
            article = cls(
                id=item['ArticleID'],
                event_notification=item.get('EventNotification', None),
                product_name=item.get('ProductName', None),
                status=item.get('Status', None))

            try:
                article.origin = Country(
                    item['OriginCountryCode'],
                    item['OriginCountry'])
            except KeyError:
                pass

            try:
                article.destination = Country(
                    item['DestinationCountryCode'],
                    item['DestinationCountry'])
            except KeyError:
                pass

            if item.get('EventCount', 0) > 0:
                article.events = Event.from_json(item['Events'])

            articles.append(article)
        return articles


class Consignment(object):

    def __init__(self, id, articles=None):
        self.id = unicode(id)
        self.articles = articles or []

    @classmethod
    def from_json(cls, json):
        try:
            consignment_json = json['ConsignmentDetails']
        except KeyError:
            return None

        consignment = cls(id=consignment_json.get('ConsignmentID'))

        if consignment_json.get('ArticleCount', 0) > 0:
            consignment.articles = Article.from_json(
                consignment.get('Articles', []))
        return consignment


class Event(object):

    def __init__(self, description, timestamp, location, signer_name=None):
        self.description = description
        self.timestamp = timestamp
        self.location = location
        self.signer_name = signer_name

    @classmethod
    def from_json(cls, json):
        events = []
        try:
            event_list = json['Event']
        except KeyError:
            return events

        for item in common.ensure_list(event_list):
            event = cls(
                description=item['EventDescription'],
                timestamp=common.get_aware_utc_datetime(
                    item['EventDateTime']),
                location=item['Location'])
            try:
                event.signer_name = item['SignerName'] or None
            except KeyError:
                pass
            events.append(event)
        return events


class Country(object):

    def __init__(self, code, name):
        self.code = code
        self.name = name

    @classmethod
    def from_json(cls, json):
        try:
            return cls(code=json['CountryCode'], name=json['CountryName'])
        except KeyError:
            raise Exception

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.code)


class Address(object):

    def __init__(self, id, addressLine1, suburb, state, postcode, country):
        self.id = unicode(id)
        self.addressLine1 = addressLine1
        self.suburb = suburb
        self.state = state
        self.postcode = postcode
        self.country = country

    @classmethod
    def from_json(cls, json):
        try:
            return cls(
                id=json['DeliveryPointIdentifier'],
                addressLine1=json['AddressLine'],
                suburb=json['SuburbOrPlaceOrLocality'],
                state=json['StateOrTerritory'],
                postcode=json['PostCode'],
                country=Country.from_json(json['Country']))
        except KeyError:
            raise Exception

    def __unicode__(self):
        return "({id}): {line1}, {suburb}, {state}, {postcode}, {country}".format(  # noqa
            id=self.id,
            line1=self.addressLine1,
            suburb=self.suburb,
            state=self.state,
            postcode=self.postcode,
            country=self.country.name)
