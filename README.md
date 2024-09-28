# Salmon Production Management System

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [API Endpoints](#api-endpoints)
- [Socket.IO Events](#socketio-events)
- [Docker](#docker)
- [Contributing](#contributing)
- [License](#license)

## Introduction
This project is a web application designed to manage orders, deliveries, and production information for a salmon production company. It includes features such as order management, delivery note generation, and real-time updates using Socket.IO.

## Features
- User authentication and role-based access control
- Order management (add, update, delete)
- Delivery note generation and printing
- Real-time updates using Socket.IO
- Responsive design with Tailwind CSS
- File uploads with Dropzone.js

## Technologies Used
- **Backend**: Flask, SQLAlchemy, Flask-SocketIO
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Database**: MySQL
- **Other**: Docker, dotenv, pandas, Pillow, Jinja2

## Installation
1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/yourproject.git
    cd yourproject
    ```

2. **Create a virtual environment**:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following:
    ```env
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=your_db_host
    DB_PORT=your_db_port
    DB_NAME=your_db_name
    SECRET_KEY=your_secret_key
    ZEBRA_PRINTER_NAME=your_printer_name
    ```

5. **Run the application**:
    ```sh
    python run.py
    ```

## Configuration
Configuration settings are managed in the `app/config.py` file. Environment variables are loaded using `dotenv`.

## Usage
To use the application, follow these steps:
1. Start the Flask server by running `python run.py`.
2. Open your web browser and navigate to `http://localhost:5000`.
3. Log in using your credentials.
4. Use the navigation menu to access different features such as order management, delivery notes, and more.

## File Structure
The project directory is structured as follows:
```
.
├── app
│ ├── blueprints
│ │ ├── deliverynote
│ │ │ ├── init.py
│ │ │ ├── views.py
│ │ ├── main
│ │ │ ├── init.py
│ │ │ ├── views.py
│ ├── static
│ │ ├── css
│ │ │ ├── base.css
│ │ │ ├── orderEditing.css
│ │ ├── js
│ │ │ ├── baseScript.js
│ │ │ ├── orderEditingScripts.js
│ │ │ ├── orderDetailsScripts.js
│ ├── templates
│ │ ├── base.html
│ │ ├── deliverynote
│ │ │ ├── delivery_note_template.html
│ │ ├── main
│ │ │ ├── index.html
│ │ ├── order
│ │ │ ├── order.html
│ │ │ ├── order_detail.html
│ │ ├── error_handling
│ │ │ ├── 403.html
│ │ │ ├── 404.html
│ │ │ ├── 500.html
│ ├── utils
│ │ ├── template_utils.py
│ ├── config.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
```


## API Endpoints
The application provides several API endpoints for managing orders, customers, and products. Here are some of the key endpoints:

- **GET /order/get-active-orders**: Fetch all active orders.
- **POST /order/add**: Add a new order.
- **POST /order/update**: Update an existing order.
- **POST /order/delete**: Delete an order.

## Socket.IO Events
The application uses Socket.IO for real-time updates. Here are some of the key events:

- **refresh_data**: Triggered to refresh data on the client side.
- **status_update**: Sends status updates to the client.

## Docker
To run the application using Docker, follow these steps:

1. **Build the Docker image**:
    ```sh
    docker build -t yourproject .
    ```

2. **Run the Docker container**:
    ```sh
    docker run -p 5000:5000 yourproject
    ```

## Contributing
Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.