from skyfield.api import wgs84, load, EarthSatellite
from datetime import datetime, timedelta, timezone
from logging_config import get_logger

"""
This module contains two classes: one modeling satellite TLE data (the name of a satellite and two lines of data about 
it), the other modeling a Satellite Event (an event where the satellite will pass overhead). 

Methods:
--------
(From Satellite)
    get_events(self, latitude, longitude, start_date, end_date, tzoffset):
        uses a satellite's TLE data and the skyfield library to generate a list of Event objects for a given satellite.
    return_satellite(self):
        returns a skyfield satellite object from my Satellite class when requested, 
        this is used to calculate a satellite's location later in the Event class.
(From Event)    
    convert_to_local_time(self):
        converts an event's time from UTC to the user's timezone. 
    date_replace(self):
        converts a date to 3 separate strings, the year, month, and day. I do this because this is the format skyfield
        accepts as arguments.
    convert_minutes_and_seconds_to_decimal(degrees):
        converts an altitude/azimuth that looks like this: 54deg 33' 03.7" to a decimal.
    convert_degrees_to_cardinal_direction(degrees):
        converts an azimuth (which represents a location relative to you, 0 being due north, 180 being south, etc.)
        to a direction. 
    return_satellite_location(self, latitude, longitude):
        returns the location data (altitude, azimuth & distance) for the satellite event. 

Constants:
----------
    TS: timescale from skyfield.api, needed to calculate satellite events.
"""

logger = get_logger(__name__)
TS = load.timescale()


class Satellite:
    def __init__(self, name, line_one, line_two):
        self._name = name
        self._line_one = line_one
        self._line_two = line_two

    @property
    def name(self):
        return self._name

    @property
    def line_one(self):
        return self._line_one

    @property
    def line_two(self):
        return self._line_two

    def __str__(self):
        return f"{self._name}\n{self._line_one}\n{self._line_two}"

    def get_events(self, latitude, longitude, start_date, end_date, tzoffset):
        """
        uses a satellite's TLE data and the skyfield library to generate a list of Event objects for a given satellite.
        :param latitude: the user's latitude
        :param longitude: the user's longitude
        :param start_date: the date to start calculating events for
        :param end_date: the date to stop calculating events on
        :param tzoffset: the user's timezone offset
        :return: a list of Event objects.
        """
        logger.info(f'generating events for satellite {self._name}')
        eph = load('de421.bsp')
        start_tokens = start_date.split('-')
        end_tokens = end_date.split('-')
        t0 = TS.utc(int(start_tokens[0]), int(start_tokens[1]), int(start_tokens[2]))
        t1 = TS.utc(int(end_tokens[0]), int(end_tokens[1]), int(end_tokens[2]))
        user_location = wgs84.latlon(float(latitude), float(longitude))
        satellite = EarthSatellite(self._line_one, self._line_two, self._name, TS)
        t, events = satellite.find_events(user_location, t0, t1, altitude_degrees=30.0)
        event_names = 'rise above 30°', 'culminate', 'set below 30°'
        sunlit = satellite.at(t).is_sunlit(eph)
        events_list = []
        for ti, event, sunlit_flag in zip(t, events, sunlit):
            e_name = event_names[event]
            state = ('in shadow', 'in sunlight')[sunlit_flag]
            # print('{:22} {:15} {}'.format(
            #     ti.utc_strftime('%Y %b %d %H:%M:%S'), name, state,
            # ))
            new_event = Event(self, ti.utc_strftime('%Y-%m-%d %H:%M:%S'), e_name, state, tzoffset)
            events_list.append(new_event)
        return events_list

    def return_satellite(self):
        """
        returns a skyfield satellite object from my Satellite class when requested,
        this is used to calculate a satellite's location later in the Event class.
        :return: a skyfield satellite object.
        """
        satellite = EarthSatellite(self._line_one, self._line_two, self._name, TS)
        return satellite


class Event:
    def __init__(self, satellite_obj, date, event_name, sunlit, tzoffset, moon_warning=None, conditions=None,
                 include_sunlit=None):
        self._satellite_obj = satellite_obj
        self._date = date
        self._event_name = event_name
        self._sunlit = sunlit
        self._timezone = float(tzoffset)
        self._moon_warning = moon_warning
        self._conditions = conditions
        self._include_sunlit = include_sunlit

    @property
    def satellite_obj(self):
        return self._satellite_obj

    @property
    def date(self):
        return self.convert_to_local_time()

    @property
    def event_name(self):
        return self._event_name

    @property
    def sunlit(self):
        return self._sunlit

    @property
    def moon_warning(self):
        return self._moon_warning

    @moon_warning.setter
    def moon_warning(self, value):
        self._moon_warning = value

    @property
    def conditions(self):
        return self._conditions

    @conditions.setter
    def conditions(self, value):
        self._conditions = value

    @property
    def include_sunlit(self):
        return self._include_sunlit

    @include_sunlit.setter
    def include_sunlit(self, value):
        self._include_sunlit = value

    def convert_to_local_time(self):
        """
        converts an event's time from UTC to the user's timezone.
        :return: the event time converted to user's timezone
        """
        # from my weather api, visual crossing, I can get a timezone offset (i.e. -05:00 for central time)
        date_dtobj = datetime.strptime(self._date, '%Y-%m-%d %H:%M:%S')
        return date_dtobj + timedelta(hours=self._timezone)  # add the time offset to the datetime object

    def __str__(self):
        # have to use self.date (the property) when referencing the date to get the localized date.
        # have to put the one with the most things at the top or else it will fire on the wrong if statement
        if self._conditions and self._moon_warning and self._include_sunlit:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t(Sunlit: {self._sunlit}, Forecast: {self._conditions})\n\t{self._moon_warning}"
        elif self._conditions and self._moon_warning:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t(Forecast: {self._conditions})\n\t{self._moon_warning}"
        elif self._conditions and self._include_sunlit:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t(Sunlit: {self._sunlit}, Forecast: {self._conditions})"
        elif self._moon_warning and self._include_sunlit:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t(Sunlit: {self._sunlit})\n\t{self._moon_warning}"
        elif self._conditions:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t(Forecast: {self._conditions})"
        elif self._moon_warning:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t{self._moon_warning}"
        elif self._include_sunlit:
            return f"At time: {self.date}, {self._satellite_obj.name} will: {self._event_name}\n\t(Sunlit: {self._sunlit})"
        else:
            return f"At time: {self.date}, {self._satellite_obj.name} will {self._event_name}"

    def date_replace(self):
        """
        converts a date to 3 separate strings, the year, month, and day. I do this because this is the format skyfield
        accepts as arguments.
        :return: 3 date tokens as described directly above.
        """
        # break up the date for use in the method below
        replace_dash = self._date.replace('-', ' ')
        replace_colon = replace_dash.replace(':', ' ')
        date_tokens = replace_colon.split()
        return date_tokens

    @staticmethod
    def convert_minutes_and_seconds_to_decimal(degrees):
        """
        converts an altitude/azimuth that looks like this: 54deg 33' 03.7" to a decimal.
        :param degrees: the degrees to convert
        :return: degrees as a decimal
        """
        # I want to convert this: 54deg 33' 03.7"
        # to this: 54 + (33/60) + (0.37/3600) (which is the degrees in decimal form)
        degrees = str(degrees)
        replace_deg = degrees.replace('deg', '')
        replace_single_quote = replace_deg.replace("'", "")
        replace_double_quote = replace_single_quote.rstrip('"')
        degree_tokens = replace_double_quote.split()
        degree_decimal = float(degree_tokens[0]) + (float(degree_tokens[1])/60) + (float(degree_tokens[2])/3600)
        return degree_decimal

    @staticmethod
    def convert_degrees_to_cardinal_direction(degrees):
        """
        converts an azimuth (which represents a location relative to you, 0 being due north, 180 being south, etc.)
        to a direction.
        :param degrees: the azimuth degrees to change into a cardinal direction
        :return: the azimuth degrees as a cardinal direction.
        """
        # 0 = north, 90 = east, 180 = south, 270 = west
        # so 22.5 = NNE , 45 = NE, 67.5 = ENE, 112.5 = ESE, 135 = SE, 157.5 = SSE, 202.5 = SSW, 225 = SW,
        # 247.5 = WSW, 292.5 = WNW, 315 = NW, 337.5 = NNW
        degrees = float(degrees)
        degrees = round(degrees)
        if degrees == 0:
            return 'North'
        elif degrees < 45:
            return 'North-North East'
        elif degrees == 45:
            return 'North East'
        elif degrees < 90:
            return "East-North East"
        elif degrees == 90:
            return "East"
        elif degrees < 135:
            return "East-South East"
        elif degrees == 135:
            return "South East"
        elif degrees < 180:
            return "South-South East"
        elif degrees == 180:
            return "South"
        elif degrees < 225:
            return "South-South West"
        elif degrees == 225:
            return "South West"
        elif degrees < 270:
            return "West-South West"
        elif degrees == 270:
            return "West"
        elif degrees < 315:
            return "West-North West"
        elif degrees == 315:
            return "North West"
        elif degrees < 360:
            return "North-North West"

    def return_satellite_location(self, latitude, longitude):
        """
        returns the location data (altitude, azimuth & distance) for the satellite event.
        :param latitude: user's latitude
        :param longitude: user's longitude
        :return: location data for this satellite event.
        """
        logger.info(f'generating satellite location for {self._satellite_obj.name}')
        # upload the user location to a format usable by skyfield api
        user_location = wgs84.latlon(float(latitude), float(longitude))
        # get the date tokens, because again, this is the format needed by skyfield
        date_tokens = self.date_replace()
        # declare event time
        event_time = TS.utc(int(date_tokens[0]), int(date_tokens[1]), int(date_tokens[2]),
                            int(date_tokens[3]), int(date_tokens[4]), int(date_tokens[5]))
        # grab satellite object from self, use return_satellite method to return a skyfield satellite object.
        satellite = self._satellite_obj.return_satellite()
        # calculate the difference between satellite and user
        difference = satellite - user_location
        # compute topocentric position
        topocentric = difference.at(event_time)
        # ask topocentric position for its altitude, azimuth, and distance
        alt, az, distance = topocentric.altaz()
        altitude = self.convert_minutes_and_seconds_to_decimal(alt)
        azimuth = self.convert_minutes_and_seconds_to_decimal(az)
        azimuth_cardinal_direction = self.convert_degrees_to_cardinal_direction(azimuth)
        location_data = f"Altitude: {altitude:.3f}°, Azimuth: {azimuth:.3f}° ({azimuth_cardinal_direction}), Distance: {distance.km:.1f} km"
        return location_data


