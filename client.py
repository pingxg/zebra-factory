import os
import socketio
from print_utils import pdf_render_print

sio = socketio.Client()

@sio.on('print')
def on_print(data):
    print("Received order ID:", data['order_id'])
    pdf_render_print(data['order_id'])

sio.connect(os.environ.get('link'))
sio.wait()