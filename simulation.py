import socket
import json
from select import select

data = [''] * 4
# Receptions des Donnees (SERVEUR UDP)
# cree une socket UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# lie la socket au port 8011 port d'ecoute
s.bind(("localhost", 8020))
s.setblocking(False)

while 1:
    # Reception de l'etat de feu de circulation depuis Arduino
    ready_to_read, _, _ = select([s], [], [],
                        0.1)  # verifi si un message est dispo dans le socket avant de recevoir le smg


    if ready_to_read:
        data, address = s.recvfrom(1024)  # format des donnees data = b'{'road1': [0, 'Y', ''], 'road2': [1, 'Y', 0], 'road3': [2, 'Y', ''], 'road4': [3, 'Y', '']}'
        data = data.decode()  # data = '{'road1': [0, 'Y', ''], 'road2': [1, 'Y', 0], 'road3': [2, 'Y', ''], 'road4': [3, 'Y', '']}'
        data = json.loads(data) # to recover the dictionnary data = {'road1': [0, 'Y', ''], 'road2': [1, 'Y', 0], 'road3': [2, 'Y', ''], 'road4': [3, 'Y', '']}
        # Iterate through the dictionary items
        for key, value in data.items():
            # Check if the value is an empty string
            if value[2] == "" or value[2] == '':
                # Replace the empty string with 0
                data[key][2] = 0

        print("+++++++++++++++++++++++++++ data : ", data)
