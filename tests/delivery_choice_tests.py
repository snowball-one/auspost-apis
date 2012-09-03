import json
import pytz

from datetime import datetime
from unittest import TestCase

from auspost.delivery_choice import (DeliveryDate,
                                     #DeliveryChoiceApi,
                                     TimeSlot,
                                     PostcodeDeliveryCapability)

class AuspostTestCase(TestCase):
    fixtures_name = None

    def setUp(self):
        self.response = None
        if self.fixture_name:
            path = 'tests/data/%s.json' % self.fixture_name
            self.response = json.load(open(path, 'r'))

class TestDeliveryEstimateDate(AuspostTestCase):
    fixture_name = 'DeliveryDates'

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
            ded.delivery_date,
            pytz.utc.localize(datetime(2012, 12, 14))
        )
        self.assertEquals(ded.working_days, 1)
        self.assertEquals(ded.timed_delivery, False)

    def test_creating_date_from_multiple_date_json_response(self):
        deds = DeliveryDate.from_json(self.response)
        self.assertEquals(len(deds), 3)

        self.assertEquals(
            deds[0].delivery_date,
            pytz.utc.localize(datetime(2011, 4, 11))
        )
        self.assertEquals(deds[0].working_days, 2)
        self.assertEquals(deds[0].timed_delivery, False)

        self.assertEquals(
            deds[1].delivery_date,
            pytz.utc.localize(datetime(2011, 4, 12))
        )
        self.assertEquals(deds[1].working_days, 3)
        self.assertEquals(deds[1].timed_delivery, True)

        self.assertEquals(
            deds[2].delivery_date,
            pytz.utc.localize(datetime(2011, 4, 13))
        )
        self.assertEquals(deds[2].working_days, 4)
        self.assertEquals(deds[2].timed_delivery, True)


class TestTimeslot(AuspostTestCase):
    fixture_name = 'DeliveryTimeslots'

    def test_creating_timeslots_from_json_response(self):
        timeslots = TimeSlot.from_json(self.response)
        self.assertEquals(len(timeslots), 5)


class TestPostcodeCapability(AuspostTestCase):
    fixture_name = 'PostcodeDeliveryCapabilities'

    def test_creating_postcode_capabilities_from_json_response(self):
        capabilities = PostcodeDeliveryCapability.from_json(self.response)
        self.assertEquals(len(capabilities), 1)

        capability = capabilities[0]
        self.assertEquals(capability.postcode, 3121)
        self.assertEquals(len(capability.days), 7)
        self.assertEquals(
            capability.last_modified.isoformat(),
            datetime(2011, 7, 29, 4, 5, 50, tzinfo=pytz.utc).isoformat()
        )
        
        expected_days = (
            ('Monday', True, True),
            ('Tuesday', True, True),
            ('Wednesday', True, True),
            ('Thursday', True, True),
            ('Friday', True, True),
            ('Saturday', False, False),
            ('Sunday', False, False),
        )

        for (day, sde, tde), day_obj in zip(expected_days, capability.days):
            self.assertEquals(day_obj.name, day)
            self.assertEquals(day_obj.standard_delivery_enabled, sde)
            self.assertEquals(day_obj.timed_delivery_enabled, tde)
