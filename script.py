import binascii
import socket

#website = input("Entrez l'adresse du site : ")
website = "google.com"

# Construction du header du message DNS
message = "AA AA 01 00 00 01 00 00 00 00 00 00"

# Construction de la query
for word in website.split('.'):
    hex_length = hex(len(word))

    # Permet d'enlever le 0x
    hex_length = hex(len(word))[2:]
    if len(hex_length) == 1:
        hex_length = '0' + hex_length

    message += " " + hex_length

    # Ajout des mots séparés par un '.'
    hex_value = bytes(word, 'utf-8').hex()
    for i in range(0, len(hex_value), 2):
        message += " " + hex_value[i] + hex_value[i+1]

# Ajout du zero byte pour finir QNAME, du QTYPE et du QCLASS
message += " 00 00 01 00 01"

# Modifier le message pour envoyer au serveur DNS
message = message.replace(" ", "").replace("\n", "")

# Envoyer le message UDP à 127.0.0.53:53
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(binascii.unhexlify(message), ("127.0.0.53", 53))
data, _ = sock.recvfrom(4096)

print(data)

sock.close() 
