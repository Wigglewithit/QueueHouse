# QueueHouse

QueueHouse is a movie tracking and recommendation web application built with Django. It allows users to keep track of movies they want to watch, organize personal watchlists, leave reviews, and discover new films.

## Features

* User registration and authentication
* Personal movie watchlists
* Mark movies as watched
* Favorite movies for quick access
* Movie reviews and ratings
* Browse and search movie collections
* Movie metadata integration
* Responsive web interface

## Built With

* Python
* Django
* SQLite
* HTML
* CSS
* JavaScript

## Installation

Clone the repository:

```bash
git clone https://github.com/Wigglewithit/QueueHouse.git
```

Move into the project directory:

```bash
cd QueueHouse
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open your browser and visit:

```text
http://127.0.0.1:8000/
```

## Project Goals

The goal of QueueHouse is to provide a simple and organized place for users to manage their movie backlog, track what they have watched, and share opinions through ratings and reviews.

This project is also being used as a learning experience for Django development, database design, authentication systems, and web application architecture.

## Future Plans

* Custom playlists
* Friend system
* User profiles
* Activity feeds
* Improved recommendations
* External movie API integrations
* Enhanced search and filtering

## License

This project is currently provided for educational and personal development purposes.
