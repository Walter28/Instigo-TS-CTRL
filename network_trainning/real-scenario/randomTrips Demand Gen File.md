++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+
+   REAL SCENARIO (DE 6h a 7h)
+
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

1. Pour la route West (496 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.west.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_west_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 7.25806451613



2. Pour la route South (67 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.south.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_south_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 53.7313432836



3. Pour la route East (232 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.east.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_east_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 15.5172413793



4. Pour la route North (94 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.north.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_north_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 38.2978723404



++++++++++++ Automatiser la modification avec un script Python ++++++++++++++++

Voici un exemple de script Python qui pourrait aider à modifier les fichiers générés :

python tripsModAutomate.py




+++++++++++++ Fusionner les fichiers de trips +++++++++++++++++++++++++++

Pour combiner tous ces fichiers de trips générés en un seul fichier de trips, vous pouvez utiliser un script Python ou un simple script bash pour concaténer les fichiers :

Script Bash pour concaténer les fichiers de trips =>

cat osm.west.modified.trips.xml osm.south.modified.trips.xml osm.east.modified.trips.xml osm.north.modified.trips.xml > osm-real-scenario.passenger.trips.xml


+++++++++++ SORT VEHICLES DEPENDING ON VEHICLES DEPART IN SIMU +++++++++++

To reorganize the XML file based on the depart attribute of the trip elements, you can use Python with the xml.etree.ElementTree module. Here’s a Python script that reads an XML file, sorts the trip elements by their depart attribute, and writes the sorted XML back to a file:

sortTrip.py

How to use this script:

    1. Save your XML content to a file (e.g., input.trips.xml):
    2. Run the Python script:

    Save the script in a file (e.g., sort_trips.py) and run it with Python:

    python sort_trips.py


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++













++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+
+   REAL SCENARIO (DE 17h a 18h)
+
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

1. Pour la route West (491 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.west.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_west_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 7.331975560081



2. Pour la route South (381 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.south.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_south_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 9.44881889763



3. Pour la route East (639 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.east.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_east_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 5.633802816901



4. Pour la route North (174 véhicules)
    python randomTrips.py -n single-intersection-new.net.xml -o osm.north.trips.xml --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"base\"" --prefix "pas_north_" --additional-file osm.add.xml --vehicle-class passenger --begin 0 --end 3600 --period 20.6895517241



++++++++++++ Automatiser la modification avec un script Python ++++++++++++++++

Voici un exemple de script Python qui pourrait aider à modifier les fichiers générés :

python tripsModAutomate.py




+++++++++++++ Fusionner les fichiers de trips +++++++++++++++++++++++++++

Pour combiner tous ces fichiers de trips générés en un seul fichier de trips, vous pouvez utiliser un script Python ou un simple script bash pour concaténer les fichiers :

Script Bash pour concaténer les fichiers de trips =>

cat osm.west.modified.trips.xml osm.south.modified.trips.xml osm.east.modified.trips.xml osm.north.modified.trips.xml > osm-real-scenario.passenger.trips.xml

NB: je ne pas utiliser ce code

+++++++++++ SORT VEHICLES DEPENDING ON VEHICLES DEPART IN SIMU +++++++++++

To reorganize the XML file based on the depart attribute of the trip elements, you can use Python with the xml.etree.ElementTree module. Here’s a Python script that reads an XML file, sorts the trip elements by their depart attribute, and writes the sorted XML back to a file:

sortTrip.py

How to use this script:

    1. Save your XML content to a file (e.g., input.trips.xml):
    2. Run the Python script:

    Save the script in a file (e.g., sort_trips.py) and run it with Python:

    python sortTrip.py


+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



