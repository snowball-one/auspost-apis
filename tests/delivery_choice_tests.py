import json
import pytz

from datetime import date, datetime, timedelta
from unittest import TestCase

from auspost.delivery_choice import *  # noqa


class AuspostTestCase(TestCase):
    fixtures = []

    def setUp(self):
        for fixture in self.fixtures:
            path = 'tests/data/%s.json' % fixture
            json_data = json.load(open(path, 'r'))
            setattr(self, fixture.lower(), json_data)


class TestDeliveryChoiceApi(TestCase):

    def setUp(self):
        self.api = DeliveryChoiceApi()

    def test_using_delivery_dates_with_invalid_from_postcode(self):
        try:
            self.api.delivery_dates('abcde', 3000, date.today())
        except common.AusPostException as exc:
            self.assertEquals(exc.code, 1001)
        else:
            self.fail("no exception raised for invalid 'from_postcode'")

    def test_using_delivery_dates_with_invalid_to_postcode(self):
        try:
            self.api.delivery_dates(3000, 'abcde', date.today())
        except common.AusPostException as exc:
            self.assertEquals(exc.code, 1002)
        else:
            self.fail("no exception raised for invalid 'to_postcode'")

    def test_using_delivery_dates_with_invalid_network_id(self):
        try:
            self.api.delivery_dates(3000, 3006, date.today(), network_id='04')
        except common.AusPostException as exc:
            self.assertEquals(exc.code, 1003)
        else:
            self.fail("no exception raised for invalid 'network_id'")

    def test_using_delivery_dates_with_invalid_date(self):
        yesterday = date.today() - timedelta(days=1)
        try:
            self.api.delivery_dates(3000, 3006, yesterday)
        except common.AusPostException as exc:
            self.assertEquals(exc.code, 1004)
        else:
            self.fail("no exception raised for invalid 'lodgement_date'")

    def test_using_delivery_dates_with_invalid_number_of_dates(self):
        try:
            self.api.delivery_dates(
                3000, 3006, date.today(), number_of_dates=0)
        except common.AusPostException as exc:
            self.assertEquals(exc.code, 1005)
        else:
            self.fail("no exception raised for invalid 'lodgement_date'")

        try:
            self.api.delivery_dates(
                3000, 3006, date.today(), number_of_dates=11)
        except common.AusPostException as exc:
            self.assertEquals(exc.code, 1005)
        else:
            self.fail("no exception raised for invalid 'lodgement_date'")


class TestDeliveryEstimateDate(AuspostTestCase):
    fixtures = ['delivery_dates']

    def test_creating_date_from_single_date_json_response(self):
        response = {
            u'DeliveryEstimateRequestResponse': {
                u'DeliveryEstimateDates': {
                    u'DeliveryEstimateDate': {
                        u'DeliveryDate': u'2012-12-14',
                        u'TimedDeliveryEnabled': False,
                        u'NumberOfWorkingDays': 1
                    }
                }
            }
        }

        deds = DeliveryDate.from_json(response)
        self.assertEquals(len(deds), 1)

        ded = deds[0]
        self.assertEquals(
            ded.delivery_date, pytz.utc.localize(datetime(2012, 12, 14)))
        self.assertEquals(ded.working_days, 1)
        self.assertEquals(ded.timed_delivery, False)

    def test_creating_date_from_multiple_date_json_response(self):
        deds = DeliveryDate.from_json(self.delivery_dates)
        self.assertEquals(len(deds), 3)

        self.assertEquals(
            deds[0].delivery_date, pytz.utc.localize(datetime(2011, 4, 11)))
        self.assertEquals(deds[0].working_days, 2)
        self.assertEquals(deds[0].timed_delivery, False)

        self.assertEquals(
            deds[1].delivery_date, pytz.utc.localize(datetime(2011, 4, 12)))
        self.assertEquals(deds[1].working_days, 3)
        self.assertEquals(deds[1].timed_delivery, True)

        self.assertEquals(
            deds[2].delivery_date, pytz.utc.localize(datetime(2011, 4, 13)))
        self.assertEquals(deds[2].working_days, 4)
        self.assertEquals(deds[2].timed_delivery, True)


class TestTimeslot(AuspostTestCase):
    fixtures = ['delivery_timeslots']

    def test_creating_timeslots_from_json_response(self):
        timeslots = TimeSlot.from_json(self.delivery_timeslots)
        self.assertEquals(len(timeslots), 5)


class TestPostcodeCapability(AuspostTestCase):
    fixtures = ['postcode_delivery_capabilities']

    def test_creating_postcode_capabilities_from_json_response(self):
        capabilities = PostcodeDeliveryCapability.from_json(
            self.postcode_delivery_capabilities
        )
        self.assertEquals(len(capabilities), 1)

        capability = capabilities[0]
        self.assertEquals(capability.postcode, 3121)
        self.assertEquals(len(capability.days), 7)
        self.assertEquals(
            capability.last_modified.isoformat(),
            datetime(2011, 7, 29, 4, 5, 50, tzinfo=pytz.utc).isoformat())

        expected_days = (
            ('Monday', True, True),
            ('Tuesday', True, True),
            ('Wednesday', True, True),
            ('Thursday', True, True),
            ('Friday', True, True),
            ('Saturday', False, False),
            ('Sunday', False, False))

        for (day, sde, tde), day_obj in zip(expected_days, capability.days):
            self.assertEquals(day_obj.name, day)
            self.assertEquals(day_obj.standard_delivery_enabled, sde)
            self.assertEquals(day_obj.timed_delivery_enabled, tde)


class TestTracking(AuspostTestCase):
    fixtures = ['tracking_article', 'tracking_multiple_articles']

    def test_creating_tracking_result_from_json(self):
        tracking_results = TrackingResult.from_json(self.tracking_article)
        self.assertEquals(len(tracking_results), 1)

        tr = tracking_results[0]
        self.assertEquals(tr.id, '1234')
        self.assertEquals(tr.consignment, None)
        self.assertEquals(tr.article.id, '1234')
        self.assertEquals(tr.article.event_notification, '00')
        self.assertEquals(tr.article.product_name, "Express Post")
        self.assertEquals(tr.article.status, "Transferred")
        self.assertEquals(len(tr.article.events), 2)

    def test_creating_multiple_tracking_results_from_json(self):
        tracking_results = TrackingResult.from_json(
            self.tracking_multiple_articles)
        self.assertEquals(len(tracking_results), 2)

        tr = tracking_results[0]
        self.assertEquals(tr.id, 'CZ299999784AU')
        self.assertEquals(tr.consignment, None)
        self.assertEquals(tr.article.id, 'CZ299999784AU')
        self.assertEquals(tr.article.event_notification, '00')
        self.assertEquals(tr.article.product_name, "International")
        self.assertEquals(tr.article.status, None)
        self.assertEquals(len(tr.article.events), 0)

        tr = tracking_results[1]
        self.assertEquals(tr.id, '12345')
        self.assertEquals(tr.consignment, None)
        self.assertEquals(tr.article.id, '12345')
        self.assertEquals(tr.article.event_notification, None)
        self.assertEquals(tr.article.product_name, None)
        self.assertEquals(tr.article.status, "Delivered")
        self.assertEquals(len(tr.article.events), 3)


class TestEvent(AuspostTestCase):
    fixtures = ['events']

    def test_creating_event_from_json(self):
        events = Event.from_json(self.events)
        self.assertEquals(len(events), 2)

        expected_events = (
            ("Transferred to",
             pytz.utc.localize(datetime(2011, 9, 4, 2, 14, 22)),
             "COFFS HARBOUR DC", None),
            ("Onboard with driver",
             pytz.utc.localize(datetime(2010, 7, 6, 1, 27, 53)),
             "ADELAIDE BC", "A POST"))

        for (desc, dt, loc, sign), event in zip(expected_events, events):
            self.assertEquals(event.description, desc)
            self.assertEquals(event.timestamp, dt)
            self.assertEquals(event.location, loc)
            self.assertEquals(event.signer_name, sign)


class TestAddressValidation(AuspostTestCase):
    fixtures = ['valid_address', 'invalid_address']

    def test_invalid_address_json_parsing(self):
        validation_result = ValidationResult.from_json(self.invalid_address)
        self.assertFalse(validation_result.is_valid)
        self.assertFalse(validation_result.has_address)

    def test_valid_address_json_parsing(self):
        validation_result = ValidationResult.from_json(self.valid_address)
        self.assertTrue(validation_result.is_valid)
        self.assertTrue(validation_result.has_address)
        self.assertEquals(
            validation_result.address.addressLine1, '109/175 Sturt St'.upper())
