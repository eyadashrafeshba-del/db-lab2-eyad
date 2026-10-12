<<<<<<< HEAD
# DB Lab 2 — Login & Registration Application

## Team Members
 Eyad Eshba 
 Ezz Elden

## Technology Stack
- **Backend:** Python + Flask
- **Database:** MySQL 
- **Frontend:** HTML + JavaScript
- **Libraries:** PyMySQL, bcrypt, python-dotenv

## How to Run

1. Install Python 3.8+
2. Install MySQL 8 and remember the root password
3. Clone: `git clone <repo-url>`
4. `cd db-lab2-eyad`
5. `pip install -r requirements.txt`
6. Run `database/schema.sql` in MySQL
7. Copy `.env.example` to `.env` and fill in your password
8. `python app.py`
9. Open http://127.0.0.1:5000

## Features Built

- R1: Register (name, email, password, confirm) ✅
- R2: Login/Logout with same error message ✅
- R3: Private welcome page ✅
- R8: Browser + server validation ✅
- R9: bcrypt hashes + parameterized queries ✅
- R10: Clean UI ✅

## Screenshots

- register.png
- login.png
- welcome.png


## Answers to Questions

(a) UPDATE/DELETE contain `AND user_id = ?` so a user can only change their own
todos. Without it, anyone could edit/delete another user's todo by sending its id.

(b) Inserting a todo with a non-existent user_id fails with error 1452 — this is
the FOREIGN KEY (referential integrity) constraint.

(c) We store a bcrypt hash, not the password, because if the DB leaks, plain
passwords are stolen and reused. bcrypt is salted and slow, so it is very hard
to reverse.

(d) NOT NULL only refuses NULL; an empty string '' is a value, so MySQL accepts
it. Only our own check can refuse an empty name.
=======
# db-lab2-eyad
>>>>>>> 382f47e273e8af5470bc838efc62053c69ff5017
