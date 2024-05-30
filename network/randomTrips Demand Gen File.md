###old
python randomTrips.py -n osm.net.xml -o osm.passenger.trips.xml --trip-attributes=" departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "pas_" --additional-file osm.add.xml --vehicle-class passenger --end 40000

python randomTrips.py -n osm.net.xml -o osm.passenger.trips.xml --trip-attributes=" departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "pas_" --additional-file osm.add.xml --vehicle-class passenger --end 40000 --period 100.0 --binomial 5


python randomTrips.py -n osm.net.xml -o osm.emergency.trips.xml --trip-attributes="guiShape=\"emergency\" departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "emer_" --additional-file osm.add.xml --vehicle-class emergency  --end 40000 --period 100.0 --binomial 50


python randomTrips.py -n osm.net.xml -o osm.police.trips.xml --trip-attributes="guiShape=\"police\" departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "pol_" --additional-file osm.add.xml --vehicle-class passenger --end 40000 --period 50.0 --binomial 25


python randomTrips.py -n osm.net.xml -o osm.fire.trips.xml --trip-attributes="guiShape=\"firebrigade\" departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "fire_" --additional-file osm.add.xml --vehicle-class emergency --end 40000 --period 100.0 --binomial 50


python randomTrips.py -n osm.net.xml -o osm.taxi.trips.xml --trip-attributes="guiShape=\"taxi\" departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "taxi_" --additional-file osm.add.xml --vehicle-class passenger --end 40000 --period 60.0 --binomial 30


python randomTrips.py -n osm.net.xml -o osm.motorcycle.trips.xml --trip-attributes="guiShape=\"motorcycle\"  departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "moto_" --additional-file osm.add.xml --vehicle-class motorcycle --end 40000 --period 7.0 --binomial 1


python randomTrips.py -n osm.net.xml -o osm.bus.trips.xml --trip-attributes="guiShape=\"bus\"  departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "bus_" --additional-file osm.add.xml --vehicle-class bus --end 40000 --period 20.0 --binomial 10


python randomTrips.py -n osm.net.xml -o osm.truck.trips.xml --trip-attributes="guiShape=\"truck\"  departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" --prefix "truck" --additional-file osm.add.xml --vehicle-class truck --end 40000 --period 17.0 --binomial 5
