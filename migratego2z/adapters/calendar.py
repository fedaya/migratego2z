
from migratego2z.go_db import CalEvent, CalCalendar, EmAccount
from typing import List
import sqlalchemy
import vobject
from time import time
from datetime import datetime

import urllib


class Calendar:
    def __init__(self, calendar: CalCalendar):
        self._events = []
        self._calendar = calendar

    def add_event(self, event: CalEvent):
        self._events.append(event)

    def get_events(self) -> List[CalEvent]:
        return self._events

    def get_event(self, name: str) -> CalEvent:
        for event in self._events:
            if event.name == name:
                return event

    def get_calendar(self) -> CalCalendar:
        return self._calendar

    def get_ical(self):
        ics = vobject.iCalendar()
        for event in self._events:
            ics.add('vevent')
            i_event = ics.contents['vevent'][len(ics.contents['vevent']) - 1]
            i_event.add('summary').value = event.name
            start_time = datetime.fromtimestamp(event.start_time, None)
            end_time = datetime.fromtimestamp(event.end_time, None)
            i_event.add('dtstart').value = start_time
            i_event.add('dtend').value = end_time
            i_event.add('status').value = event.status
            if event.description != '' and event.description is not None:
                i_event.add('description').value = event.description
            if event.location != '' and event.location is not None:
                i_event.add('location').value = event.location
            i_event.add('transp').value = 'OPAQUE' if event.busy == 1 else 'TRANSPARENT'
            if event.rrule != '' and event.rrule is not None:
                i_event.add('rrule').value = event.rrule
            i_event.add('class').value = 'PUBLIC' if event.private == 0 else 'PRIVATE'
            i_event.add('uid').value = event.uuid
            if event.mtime != 0:
                i_event.add('dtstamp').value = datetime.fromtimestamp(event.mtime, tz=None)
            elif event.ctime != 0:
                    i_event.add('dtstamp').value = datetime.fromtimestamp(event.ctime, tz=None)
            else:
                i_event.add('dtstamp').value = datetime(time.time())
        return ics.serialize()


def create_calendar(calendar: CalCalendar, events: sqlalchemy.engine.ResultProxy) -> Calendar:
    this_calendar = Calendar(calendar)
    for event in events:
        this_calendar.add_event(event)
    return this_calendar


def extract_calendar_list(connection: sqlalchemy.engine.Connection, user: EmAccount) -> List[Calendar]:
    query = sqlalchemy.select([CalCalendar]).where(CalCalendar.user_id == user.user_id)
    calendars = connection.execute(query)
    return_cals = []
    for calendar in calendars:
        query = sqlalchemy.select([CalEvent]).where(CalEvent.calendar_id == calendar.id)
        results = connection.execute(query)
        return_cals.append(create_calendar(calendar, results))
    return return_cals


def export_calendars_from_user(connection: sqlalchemy.engine.Connection, user: EmAccount, base_name: str) -> str:
    calendars = extract_calendar_list(connection, user)
    return_string = ""
    for calendar in calendars:
        ical = calendar.get_ical()
        filename = base_name + '.' + calendar.get_calendar().name + '.' + user.username + '.ics'
        file = open(filename, "wb")
        file.write(ical.encode('utf-8'))
        file.close()
        return_string += "selectMailbox -A "+user.username+"\n"
        return_string += "createFolder --view appointment \'/Calendar/" + calendar.get_calendar().name + "\'\n"
        return_string += "postRestUrl \"/Calendar/" + urllib.parse.quote(string=calendar.get_calendar().name,
                                                                         encoding='ascii',
                                                                         errors='xmlcharrefreplace') + \
                         "?fmt=ics\" \"" + filename + "\"\n"
    return return_string
