import os
import time
import threading

import socketio
import logging
from print_utils import pdf_render_print


# Set up logging with timestamp
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    """Callback for when the client successfully connects to the server."""
    logger.info("Connected to the server.")

@sio.on('disconnect')
def on_disconnect():
    """Callback for when the client disconnects from the server."""
    logger.info("Disconnected from the server. Trying to reconnect...")
    sio.connect() # Add reconnection attempt

@sio.on('print_zebra')
def on_print(data):
    """Callback for handling 'print_zebra' events from the server."""
    order_id = data.get('order_id')
    if order_id:
        logger.info(f"Received order ID: {order_id}. Printing Zebra label.")
        try:
            pdf_render_print(order_id, file_type="zpl")
        except Exception as e:
            logger.error(f"Error while processing order ID {order_id}: {e}")
    else:
        logger.warning("Received 'print_zebra' event without order ID.")

@sio.on('print_pdf')
def on_print(data):
    """Callback for handling 'print_pdf' events from the server."""
    order_id = data.get('order_id')
    if order_id:
        logger.info(f"Received order ID: {order_id}. Printing PDF.")
        try:
            pdf_render_print(order_id, file_type="pdf")
        except Exception as e:
            logger.error(f"Error while processing order ID {order_id}: {e}")
    else:
        logger.warning("Received 'print_pdf' event without order ID.")


@sio.on('keepalive_response')
def on_keepalive_response(data):
    """Callback for handling the server's response to our keepalive message."""
    logger.info("Received keepalive response from server.")

def keepalive_loop():
    """Continuously send keepalive messages to the server."""
    while True:
        time.sleep(5)  # Send a keepalive message every 10 seconds
        sio.emit('keepalive', {})
        logger.info("Sending keepalive message to the server.")


def main():
    """Main function to start the client."""
    link = os.environ.get('LINK')
    if not link:
        logger.error("Environment variable 'link' not set.")
        return

    try:
        sio.connect(link)
        
        # Start the keepalive loop in a separate thread
        keepalive_thread = threading.Thread(target=keepalive_loop)
        keepalive_thread.start()

        sio.wait()
    except Exception as e:
        logger.error(f"Error connecting to server: {e}")

if __name__ == "__main__":
    main()
