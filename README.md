
## Title 
 
Library Management System API

## Description

This project is a simple library management system built with Flask, SQLAlchemy, and JWT for authentication. It allows administrators to manage users, books, and borrowing requests. Users can submit borrow requests, and admins can approve or deny these requests.


## Features
- Admin user creation
- Borrow request management (approval/denial)
- Book inventory management
- User borrow history tracking
- JWT authentication for secure access
- SQLite database with SQLAlchemy ORM
## Tech Stack

**Backend:** Flask ,Flask-Sqalchemy ,Flask-MIgrate

**Database:** SQLite (or replace with PostgreSQL/MySQL if desired)


## Installation

1.Prerequisites :

```bash
  - Python 3.7+
  - pip (Python package installer)
  - SQLite (or another database you prefer, though the app is configured for SQLite by default)
```

2.Steps to Set Up :

```bash
Create a virtual environment          :    python3 -m venv < name of virtual Environment > 
 	
To activate the virtual Environment   :    < name of virtual Environment >/Scripts/activate 
 
Install dependencies                  :    pip install -r requirements.txt
 
Set up the database                   :    flask db init
                                           flask db migrate -m "Initial migration"
                                           flask db upgrade
 
Run the server                        :    Python app.py 
 
* The application will start and be accessible at http://127.0.0.1:5000

   ```

3.Running the Application with Docker : 

```bash
Build the Docker image              :     docker build -t < name of image > .
 
Run the Docker container            :     docker run -p 5000:5000 < name of Image >
  
* The application will be available at http://localhost:5000

```
4.Structure of the application :

```bash
 /Stack
 ├── app/
 │   ├── models.py        		   
 │   ├── routes.py         		   
 |   ├── __init__.py        			 
 ├── requirements.txt       
 ├── Dockerfile         				
 ├── migrations/        				
 ├── app.py             			      
 └── README.md              		    
 ```

 5.Other Info :

--> Error Handling: The application returns appropriate HTTP 400 status codes for bad requests, such as when a book is unavailable or a student has already issued the maximum number of books.

--> Modularity: The application is designed to be modular, with separate services handling business logic, making the codebase easy to maintain and extend.

--> Docker Support: A Dockerfile is included for containerization, making it easy to deploy the application in different environments.

 
## Documentation

[Python_Documentation](https://docs.python.org/3/)

[Flask_Documentation](https://flask.palletsprojects.com/en/stable/)

[SQLite_Documentation](https://www.sqlite.org/docs.html)



