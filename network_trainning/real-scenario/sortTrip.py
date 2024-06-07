import xml.etree.ElementTree as ET

def sort_trips_by_depart(xml_file, output_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract the trip elements and sort them by the depart attribute
    trips = root.findall('trip')
    trips_sorted = sorted(trips, key=lambda trip: float(trip.get('depart')))

    # Clear existing trips and append the sorted ones
    for trip in root.findall('trip'):
        root.remove(trip)
    
    for trip in trips_sorted:
        root.append(trip)

    # Write the sorted XML to the output file
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

# Example usage
input_file = 'osm.passenger.trips.xml'
output_file = 'sorted_osm-real-scenario.passenger.trips.xml'
sort_trips_by_depart(input_file, output_file)
