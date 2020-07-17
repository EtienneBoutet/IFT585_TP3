import binascii
import socket
from bs4 import BeautifulSoup

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

# Retourne les headers et le contenu parsé
def send_and_receive(sock, website, path="/"):
    http_message = b"HEAD /" + bytes(path, 'utf-8') + b" HTTP/1.1\r\nHost: "+ bytes(website, 'utf-8') + b"\r\nConnection: keep-alive\r\nUser-agent: Mozilla/4.0\r\nAccept: text/html, image/gif, image/jpeg, image/tiff\r\n\r\n"
    
    sock.sendall(http_message)
    
    head = sock.recv(20000)

    # Trouver la taille de contenu
    content_length = 0
    for header in head.split(b"\r\n"):
        if b"Content-Length" in header:
            content_length = int(header.split(b":")[1][1:])

    http_message = b"GET " + bytes(path, 'utf-8') + b" HTTP/1.1\r\nHost: "+ bytes(website, 'utf-8') + b"\r\nConnection: keep-alive\r\nUser-agent: Mozilla/4.0\r\nAccept: text/html, image/gif, image/jpeg, image/tiff\r\n\r\n"
    sock.sendall(http_message)

    data = b""

    chunks = []
    bytes_recd = 0
    while bytes_recd < content_length:
        chunk = sock.recv(min(content_length - bytes_recd, 2048))
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)

    chunks.append(sock.recv(2048))

    data += b''.join(chunks)

    return data

website = input("Entrez l'adresse du site : ")

print("=================================================================")
print("DNS REQUEST")
print("=================================================================")

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

print("Sending DNS message to 8.8.8.8:53\n")
sock.sendto(binascii.unhexlify(message), ("8.8.8.8", 53))
data, _ = sock.recvfrom(4096)

# Transformer la réponse en string d'hexadécimal.
data = data.hex()

sock.close() 

# Parser la section header
response_header = data[0:24]

# Parser la section question
name_length = int(data[24:26], 16)
domain_length = int(data[24 + 2*name_length + 2: 24 + 2*name_length + 4], 16)
end_of_question = 26 + 2*name_length + 2*domain_length + 12
question_section = data[24: end_of_question]

# Parser la section 
answer_section = data[end_of_question:]

# Vérification des erreurs.
if response_header[7] != '0':
    print(dns_error_parser(response_header[7]))
    exit()

print("RCODE : 0 - DNS Query completed succesfully.\n")

# Trouver et parser l'adresse IP
ip_address_hex = answer_section[-8:]
ip_address = ""
for i in range(0, len(ip_address_hex), 2):
    ip_address += str(int(ip_address_hex[i] + ip_address_hex[i+1], 16)) + "."
ip_address = ip_address[:-1] 

print("Address IP is : " + ip_address + "\n")

# Se connecter en TCP au serveur web
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((ip_address, 80))

# Envoyer la requête HTTP au serveur web
data = send_and_receive(sock, website)

headers, _, body = data.partition(b'\r\n\r\n')
headers = headers.decode('latin1')

print("=================================================================")
print("HTTP REQUEST")
print("=================================================================")
print("Web server response :\n")
print("Status : " + headers.split("\r\n")[0] + "\n")

print("Headers : ")
print("\r\n".join(headers.split("\r\n")[1:]) + "\n")

input()

print("Content : ")
print(body)

# Télécharger les images (si présentes)
soup = BeautifulSoup(body, 'html.parser')
img_tags = soup.find_all('img')

urls = [img['src'] for img in img_tags]

if len(urls) == 0:
    exit()


for index, url in enumerate(urls):
    if url[-3:] == "jpg" or url[-3:] == "gif":
        if url[0] != "/":
            url = "/" + url
        data = send_and_receive(sock, website, url)
        _, _, body = data.partition(b'\r\n\r\n')
        f = open(str(index) + "." + url[-3:], 'wb')
        f.write(body)
        f.close()
