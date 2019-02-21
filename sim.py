from collections import defaultdict, Counter
import datetime
import json
from pprint import pprint


def simulate(train, station_order):
    """
    determines number of trips between each station for a given train
    """
    stations = station_order[train["line"]].copy()
    if train["direction"] == "Outbound":
        stations.reverse()
    boarded_station = {}
    trips = {}
    for i in range(len(stations)):
        if stations[i] in train["stations"]:
            boarded_station[stations[i]] = train["stations"][stations[i]]["ons"]
            offs = train["stations"][stations[i]]["offs"]
            for j in range(1, i+1):
                if offs == 0:
                    break
                if stations[i-j] in boarded_station:
                    if boarded_station[stations[i-j]] >= offs:
                        boarded_station[stations[i-j]] -= offs
                        trips[(stations[i-j], stations[i])] = offs
                        offs = 0
                    else:
                        local_offs = boarded_station[stations[i-j]]
                        boarded_station[stations[i-j]] = 0
                        trips[(stations[i-j], stations[i])] = local_offs
                        offs -= local_offs
    return trips


def get_trains(filename, begin_in, end_in, begin_out, end_out):
    """
    finds trains matching time criteria
    """
    with open(filename, 'r') as infile:
        all_trains = json.load(infile)
    trains = {}
    for train in all_trains:
        if all_trains[train]["direction"] == "Inbound":
            if "North Station" in all_trains[train]["stations"]:
                time = all_trains[train]["stations"]["North Station"]["time"]
                time = datetime.time(*map(int, time.split(':')))
                if time < begin_in or time > end_in:
                    trains[train] = all_trains[train]
            if "South Station" in all_trains[train]["stations"]:
                time = all_trains[train]["stations"]["South Station"]["time"]
                time = datetime.time(*map(int, time.split(':')))
                if time < begin_in or time > end_in:
                    trains[train] = all_trains[train]
        if all_trains[train]["direction"] == "Outbound":
            if "North Station" in all_trains[train]["stations"]:
                time = all_trains[train]["stations"]["North Station"]["time"]
                time = datetime.time(*map(int, time.split(':')))
                if time < begin_out or time > end_out:
                    trains[train] = all_trains[train]
            if "South Station" in all_trains[train]["stations"]:
                time = all_trains[train]["stations"]["South Station"]["time"]
                time = datetime.time(*map(int, time.split(':')))
                if time < begin_out or time > end_out:
                    trains[train] = all_trains[train]
    return trains


def zone_converter(trips, zones):
    """
    takes number of trips between each station and returns number of trips
    between each zone
    """
    zone_trips = defaultdict(int)
    for trip in trips:
        zone_trips[(zones[trip[0].lower()], zones[trip[1].lower()])] += trips[trip]
    return zone_trips


def get_fare(trip, fares):
    """
    gets fare between two zones
    trip is in this format:
    (x, y) -> x = starting zone; y = ending zone
    """
    if trip[0] == 0:
        return fares["zone"][str(trip[1])]
    elif trip[1] == 0:
        return fares["zone"][str(trip[0])]
    else:
        return fares["interzone"][str(abs(trip[0] - trip[1]))]


if __name__ == "__main__":
    # define peak
    begin_in = datetime.time(hour=4, minute=0)  # begin inbound peak
    end_in = datetime.time(hour=10, minute=0)   # end inbound peak
    begin_out = datetime.time(hour=15, minute=30)   # begin outbound peak
    end_out = datetime.time(hour=19, minute=0)      # end outbound peak
    # get desired trains from data
    trains = get_trains("data.json", begin_in, end_in, begin_out, end_out)
    # load ordered lists of stations
    with open('line.json', 'r') as infile:
        station_order = json.load(infile)
    # get station-zone pairings
    with open('zones.json', 'r') as infile:
        zones = json.load(infile)
    # get fare info
    with open('fares2.json', 'r') as infile:
        fares = json.load(infile)
    # find number of trips between each zone
    zone_trips = Counter()
    for train in trains:
        zone_trips += Counter(zone_converter(simulate(trains[train], station_order), zones))
    zone_trips = dict(zone_trips)
    # calculate costs
    original_cost = {trip: zone_trips[trip] * get_fare(trip, fares["normal"])
                     for trip in zone_trips}
    reduced_cost = {trip: zone_trips[trip] * get_fare(trip, fares["reduced"])
                    for trip in zone_trips}
    difference = {trip: original_cost[trip] - reduced_cost[trip]
                  for trip in zone_trips}
    all_costs = {trip: [original_cost[trip], reduced_cost[trip], difference[trip]]
                 for trip in zone_trips}
    # print results
#    pprint(zone_trips)
#    pprint(all_costs)
    print("trips:", sum(zone_trips.values()))
    print("original cost:", sum(original_cost.values()))
    print("reduced cost:", sum(reduced_cost.values()))
    print("difference:", sum(difference.values()))
