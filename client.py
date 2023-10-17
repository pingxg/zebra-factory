import socketio
from print_utils import print_document, print_zebra


sio = socketio.Client()


@sio.on('print')
def on_print(data):
    print("Received data:", data['data'])
    # print_zebra(data['data'])
    # print_document("C:/Users/PingxinGao/Downloads/Nihtisilta 4, 02630 Espoo.pdf")

sio.connect('https://zebra-factory.onrender.com')
sio.wait()