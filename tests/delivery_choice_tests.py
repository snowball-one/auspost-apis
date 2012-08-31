import json 
from datetime import datetime
from unittest import TestCase

from auspost_apis.delivery_choice import (DeliveryDate,
                                          DeliveryChoiceApi,
                                          TimeSlot)


class TestDeliveryEstimateDate(TestCase):

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
        self.assertEquals(ded.delivery_date, datetime(2012, 12, 14))
        self.assertEquals(ded.working_days, 1)
        self.assertEquals(ded.timed_delivery, False)

    def test_creating_date_from_multiple_date_json_response(self):
        response = json.load(open('tests/data/deliverydates.json', 'r'))

        deds = DeliveryDate.from_json(response)
        self.assertEquals(len(deds), 3)

        self.assertEquals(deds[0].delivery_date, datetime(2011, 4, 11))
        self.assertEquals(deds[0].working_days, 2)
        self.assertEquals(deds[0].timed_delivery, False)

        self.assertEquals(deds[1].delivery_date, datetime(2011, 4, 12))
        self.assertEquals(deds[1].working_days, 3)
        self.assertEquals(deds[1].timed_delivery, True)

        self.assertEquals(deds[2].delivery_date, datetime(2011, 4, 13))
        self.assertEquals(deds[2].working_days, 4)
        self.assertEquals(deds[2].timed_delivery, True)


class TestTimeslot(TestCase):

    def test_creating_timeslots_from_json_response(self):
        response = json.load(open('tests/data/deliverytimeslots.json', 'r'))

        timeslots = TimeSlot.from_json(response)

        self.assertEquals(len(timeslots), 5)
