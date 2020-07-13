import binascii
import socket

def format_hex(hex):
    octets = [hex[i:i+2] for i in range(0, len(hex), 2)]
    pairs = [" ".join(octets[i:i+2]) for i in range(0, len(octets), 2)]
    return "\n".join(pairs)

def dns_error_parser(code):
    message = "DNS Error : "

    if code == '1':
        message += "DNS Query Format Error."
    elif code == '2':
        message += "Server failed to complete the DNS request."
    elif code == '3':
        message += "Domain name does not exist."
    elif code == '4':
        message += "Function not implemented."
    elif code == '5':
        message += "The server refused to answer for the query."
    elif code == '6':
        message += "Name that should not exist, does exist."
    elif code == '7':
        message += "RRset that should not exist, does exist."
    elif code == '8':
        message += "Server not authoritative for the zone."
    elif code == '9':
        message += "Name not in zone." 

    return message


website = input("Entrez l'adresse du site : ")
#website = "google.com"

# Construction du header du message DNS
message = "AA AA 01 00 00 01 00 00 00 00 00 00"

# Construction de la query
for word in website.split('.'):
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

sock.sendto(binascii.unhexlify(message), ("8.8.8.8", 53))
data, _ = sock.recvfrom(4096)

# Transformer la réponse en string d'hexadécimal.
data = data.hex()

sock.close() 

# Parser la réponse
response_header = data[4:8]

# Vérification des erreurs.
if response_header[3] != '0':
    print(dns_error_parser(response_header[3]))
    # TODO - Trouver erreur
    exit()

print("RCODE : 0 - DNS Query completed succesfully.")

ip_address_length = int(data[76:80], 16)

# Trouver et parser l'adresse IP
ip_address_hex = data[(-2) * ip_address_length:]
ip_address = ""
for i in range(0, len(ip_address_hex), 2):
    ip_address += str(int(ip_address_hex[i] + ip_address_hex[i+1], 16)) + "."
ip_address = ip_address[:-1] 

print(ip_address)
