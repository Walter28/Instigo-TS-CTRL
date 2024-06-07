import xml.etree.ElementTree as ET
import random

def modify_trips(input_file, output_file, from_edges, to_edges):
    tree = ET.parse(input_file)
    root = tree.getroot()

    trips = root.findall('trip')
    for trip in trips:
        trip.set('from', from_edges[0])
        trip.set('to', random.choice(to_edges))

    tree.write(output_file)

modify_trips('osm.west.trips.xml', 'osm.west.modified.trips.xml', ['w_t'], ['t_e', 't_n', 't_s'])
modify_trips('osm.south.trips.xml', 'osm.south.modified.trips.xml', ['s_t'], ['t_w', 't_n', 't_e'])
modify_trips('osm.east.trips.xml', 'osm.east.modified.trips.xml', ['e_t'], ['t_w', 't_n', 't_s'])
modify_trips('osm.north.trips.xml', 'osm.north.modified.trips.xml', ['n_t'], ['t_w', 't_s', 't_e'])

with open('osm.passenger.trips.xml', 'w') as outfile:
    for fname in ['osm.west.modified.trips.xml', 'osm.south.modified.trips.xml', 'osm.east.modified.trips.xml', 'osm.north.modified.trips.xml']:
        with open(fname) as infile:
            outfile.write(infile.read())
