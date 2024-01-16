from datetime import datetime, timedelta

"""
This module provides functions to filter satellite event data in various ways based on the user's selections from the
gui.

Methods:
--------
    convert_datetime_to_str_tokens(datetime_obj):
        takes a datetime object, converts it into two strings: one being the date only, the other the time only. 
    round_datetime_to_exact_hour(datetime_obj):
        rounds a datetime object to an exact hour (e.g. 06:34 = 06:00) if minute > 45, will round to next hour.
    filter_only_sunlit_events(events):
        filters results and removes any where the satellite is within the Earth's shadow.
    add_sunlit_to_events(events):
        adds text describing if a satellite is in Earth's shadow or in sunlight to each event.
    filter_only_at_night(events, forecasts):
        filters events and only returns those that occur between user's local sunset & sunrise times for the event date.
    add_conditions(events, forecasts):
        adds hourly forecast conditions (i.e. clear, partly cloudy, etc.) to the events
    filter_for_clouds(events, forecasts):
        filters out all events that do not occur during clear skies. 
    set_moon_warnings(events, forecasts):
        attaches a warning to any event where the moon is visible and more than 50% full (using daily moonrise/set 
        times)
    filter_for_moon(events, forecasts):
        removes any event that would have a moon warning, i.e. any event where the moon is visible and more than 50% 
        full (using daily moonrise/set times)

Constants:
----------
    FIRST_QUARTER: the first quarter of the moon phase
    LAST_QUARTER: the last quarter of the moon phase
"""

FIRST_QUARTER = 0.25
LAST_QUARTER = 0.75


def convert_datetime_to_str_tokens(datetime_obj):
    """
    takes a datetime object, converts it into two strings: one being the date only, the other the time only. Date is
    date_tokens[0], time is date_tokens[1].
    :param datetime_obj: datetime object you would like to split into 2 strings
    :return: two strings: one being the date only, the other the time only. (they're tokens, so within the same object)
    """
    date_str = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    date_tokens = date_str.split()
    return date_tokens


def round_datetime_to_exact_hour(datetime_obj):
    """
    rounds a datetime.time object to an exact hour (e.g. 06:34 = 06:00) if minute > 45, will round to next hour.
    :param datetime_obj: datetime.time object you would like to round. (%H:%M:%S ONLY)
    :return: rounded datetime.time object.
    """
    # grab the minutes and seconds from our argument
    time_to_discard = timedelta(minutes=datetime_obj.minute,
                                seconds=datetime_obj.second)
    # subtract it from our argument
    rounded_dt = datetime_obj - time_to_discard
    # I don't think 45 is a magic number here, because the parameter name describes exactly what it is.
    if time_to_discard > timedelta(minutes=45):
        # might as well round up to the next hour if we are that close...
        rounded_dt += timedelta(hours=1)
        return rounded_dt.time()
    return rounded_dt.time()


def filter_only_sunlit_events(events):
    """
    filters results and removes any where the satellite is within the Earth's shadow.
    :param events: a list of satellite Event objects.
    :return: all events where the satellite is lit by the sun.
    """
    new_events_list = []
    for event in events:
        if event.sunlit == 'in sunlight':
            new_events_list.append(event)
    return new_events_list


def add_sunlit_to_events(events):
    """
    adds text describing if a satellite is in Earth's shadow or in sunlight to each event.
    :param events: a list of satellite Event objects.
    :return: that same list of events, but now their __str__ method will return whether the satellite is sunlit or not.
    """
    for event in events:
        event.include_sunlit = 1
    return events


def filter_only_at_night(events, forecasts):
    """
    filters events and only returns those that occur between user's local sunset & sunrise times for the event date.
    :param events: a list of satellite Event objects
    :param forecasts: a list of Forecast objects
    :return: a new list, with only events that occur at night.
    """
    new_events_list = []
    for event in events:
        # need to convert the event date to strings, so I can split the date & time apart.
        event_date_tokens = convert_datetime_to_str_tokens(event.date)
        # but, of course, I need to convert the time back to a datetime, so I can use operators on it!
        local_event_time_dtobj = datetime.strptime(event_date_tokens[1], "%H:%M:%S").time()
        for forecast in forecasts:
            if forecast.date == event_date_tokens[0]:
                sunrise = datetime.strptime(forecast.sunrise, "%H:%M:%S").time()
                sunset = datetime.strptime(forecast.sunset, "%H:%M:%S").time()
                if local_event_time_dtobj < sunrise or local_event_time_dtobj > sunset:
                    new_events_list.append(event)
    return new_events_list


def add_conditions(events, forecasts):
    """
    adds hourly forecast conditions (i.e. clear, partly cloudy, etc.) to the events
    :param events: a list of satellite event objects.
    :param forecasts: a list of forecast objects.
    :return: the same list of events, but now their __str__ method will return the hourly forecast conditions as well.
    """
    for event in events:
        event_date_tokens = convert_datetime_to_str_tokens(event.date)
        local_event_time_dtobj = datetime.strptime(event_date_tokens[1], "%H:%M:%S")  # round function covers .time()
        rounded_local_event_time = round_datetime_to_exact_hour(local_event_time_dtobj)
        for forecast in forecasts:
            if forecast.date == event_date_tokens[0]:
                for key, value in forecast.hourly_conditions_dict.items():
                    # the local event time is a datetime, so I have to convert one of them...
                    key_dtobj = datetime.strptime(key, "%H:%M:%S").time()
                    if key_dtobj == rounded_local_event_time:
                        event.conditions = value
    return events


def filter_for_clouds(events, forecasts):
    """
    filters out all events that do not occur during clear skies.
    :param events: a list of satellite event objects.
    :param forecasts: a list of forecast objects.
    :return: a list of event objects that occur during clear skies.
    """
    new_events_list = []
    for event in events:
        event_date_tokens = convert_datetime_to_str_tokens(event.date)
        local_event_time_dtobj = datetime.strptime(event_date_tokens[1], "%H:%M:%S")  # round function covers .time()
        rounded_local_event_time = round_datetime_to_exact_hour(local_event_time_dtobj)
        for forecast in forecasts:
            if forecast.date == event_date_tokens[0]:
                for key, value in forecast.hourly_conditions_dict.items():
                    key_dtobj = datetime.strptime(key, "%H:%M:%S").time()
                    if key_dtobj == rounded_local_event_time:
                        if value == 'Clear':
                            new_events_list.append(event)
    return new_events_list


def set_moon_warnings(events, forecasts):
    """
    attaches a warning to any event where the moon is visible and more than 50% full (using daily moonrise/set
        times)
    :param events: a list of satellite event objects.
    :param forecasts: a list of forecast objects.
    :return: the same list of events, but now their __str__ method returns a warning if the moon is as described above.
    """
    for event in events:
        # split each event date into 2 parts
        event_date_tokens = convert_datetime_to_str_tokens(event.date)
        # grab just the time from that event date.
        local_event_time_dtobj = datetime.strptime(event_date_tokens[1], "%H:%M:%S").time()
        i = 0
        for forecast in forecasts:
            # need to convert both of them to datetime because I got bad results comparing strings elsewhere in the code
            forecast_date_dtobj = datetime.strptime(forecast.date, "%Y-%m-%d").date()
            event_date_dtobj = datetime.strptime(event_date_tokens[0], "%Y-%m-%d").date()
            if forecast_date_dtobj == event_date_dtobj:
                # sometimes the api does not return a moonset/moonrise time, so I have to account for that...
                if forecast.moonset != 0 and forecast.moonrise != 0:
                    moon_rise_dtobj = datetime.strptime(forecast.moonrise, "%Y-%m-%d %H:%M:%S")
                    moon_set_dtobj = datetime.strptime(forecast.moonset, "%Y-%m-%d %H:%M:%S")
                    # I also need to check if the event has occurred before the moonset from the previous night...
                    # because python allows negative indicies, this will work no matter what, but I will not check
                    # unless i != 0...
                    previous_day_moon_set_dtobj = datetime.strptime(forecasts[i-1].moonset, "%Y-%m-%d %H:%M:%S")
                    sunrise = datetime.strptime(forecast.sunrise, "%H:%M:%S").time()
                    sunset = datetime.strptime(forecast.sunset, "%H:%M:%S").time()
                    if local_event_time_dtobj > sunset or local_event_time_dtobj < sunrise:
                        # if it is closer to a full moon than not...
                        if forecast.moonphase > FIRST_QUARTER or forecast.moonphase < LAST_QUARTER:
                            if moon_rise_dtobj < event.date < moon_set_dtobj:
                                event.moon_warning = f'Moon is {forecast.translate_moonphase()}, satellite may be obscured. (moon set: {moon_set_dtobj})'
                                i += 1
                            elif i != 0 and event.date < previous_day_moon_set_dtobj:
                                event.moon_warning = f'Moon is {forecast.translate_moonphase()}, satellite may be obscured. (moon set: {previous_day_moon_set_dtobj})'
                                i += 1
                        else:
                            # need to increment i no matter what...
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
    return events


def filter_for_moon(events, forecasts):
    """
    removes any event that would have a moon warning, i.e. any event where the moon is visible and more than 50%
        full (using daily moonrise/set times)
    :param events: a list of satellite event objects.
    :param forecasts: a list of forecast objects.
    :return: a list of events where the moon is not as described above.
    """
    # for the most part this is the same as the method above.
    bad_event_list = []
    for event in events:
        event_date_tokens = convert_datetime_to_str_tokens(event.date)
        local_event_time_dtobj = datetime.strptime(event_date_tokens[1], "%H:%M:%S").time()
        i = 0
        for forecast in forecasts:
            forecast_date_dtobj = datetime.strptime(forecast.date, "%Y-%m-%d").date()
            event_date_dtobj = datetime.strptime(event_date_tokens[0], "%Y-%m-%d").date()
            if forecast_date_dtobj == event_date_dtobj:
                if forecast.moonset != 0 and forecast.moonrise != 0:
                    moon_rise_dtobj = datetime.strptime(forecast.moonrise, "%Y-%m-%d %H:%M:%S")
                    moon_set_dtobj = datetime.strptime(forecast.moonset, "%Y-%m-%d %H:%M:%S")
                    previous_day_moon_set_dtobj = datetime.strptime(forecasts[i-1].moonset, "%Y-%m-%d %H:%M:%S")
                    sunrise = datetime.strptime(forecast.sunrise, "%H:%M:%S").time()
                    sunset = datetime.strptime(forecast.sunset, "%H:%M:%S").time()
                    if local_event_time_dtobj > sunset or local_event_time_dtobj < sunrise:
                        if forecast.moonphase > FIRST_QUARTER or forecast.moonphase < LAST_QUARTER:
                            if moon_rise_dtobj < event.date < moon_set_dtobj:
                                bad_event_list.append(event)
                                i += 1
                            elif i != 0 and event.date < previous_day_moon_set_dtobj:
                                bad_event_list.append(event)
                                i += 1
                        else:
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
    good_event_list = [x for x in events if x not in bad_event_list]
    return good_event_list


