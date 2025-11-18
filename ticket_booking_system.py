import mysql.connector
import tabulate
import csv
import random
import os
from datetime import date, datetime
import calendar

db = mysql.connector.connect(user='root', password='sql123', host='localhost')

if db.is_connected():
    print("Connection successful")


def ensure_connected():
    global db
    try:
        db = mysql.connector.connect(
            user='root', password='sql123', host='localhost', database='movie'
        )
    except:
        init_database()


def init_database():
    cur = db.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS movie")
    ensure_connected()


def create_client_table(flag):
    global db
    db = mysql.connector.connect(
        user='root', password='sql123', host='localhost', database='movie'
    )
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS client(
            ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            Username VARCHAR(200) NOT NULL,
            Password VARCHAR(200) NOT NULL
        )
    """)
    if flag != "dry":
        admin_menu(flag)


def create_admin_table():
    global db
    ensure_connected()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE admin(
            ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            Username VARCHAR(200) NOT NULL,
            Password VARCHAR(200) NOT NULL
        )
    """)
    cur.execute("INSERT INTO admin(Username, Password) VALUES('admin','admin')")
    db.commit()


def create_movie_table():
    ensure_connected()
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE movie(
            ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            Title VARCHAR(200),
            Genre VARCHAR(200),
            Rating FLOAT,
            ReleaseDate DATE,
            Price INT
        )
    """)


def create_booking_csv(flag):
    with open("booking.csv", "w"):
        pass
    print("booking.csv file created")
    if flag != "dry":
        admin_menu(flag)


def dry_start():
    init_database()
    create_admin_table()
    create_client_table("dry")
    create_movie_table()
    create_booking_csv("dry")
    main_menu()


def login_client():
    ensure_connected()
    user = input("Username: ")
    pw = input("Password: ")
    cur = db.cursor()
    cur.execute("SELECT * FROM client")
    rows = cur.fetchall()

    for row in rows:
        if row[1] == user and row[2] == pw:
            print(f"Welcome {user} to SSPVR")
            return row[0]

    print("Invalid credentials")
    client_menu()


def login_admin():
    ensure_connected()
    user = input("Username: ")
    pw = input("Password: ")

    cur = db.cursor()
    cur.execute("SELECT * FROM admin")
    rows = cur.fetchall()

    for row in rows:
        if row[1] == user and row[2] == pw:
            print(f"Welcome {user}, Admin")
            admin_menu(row[0])
            return

    print("Invalid credentials")
    main_menu()


def register_client():
    ensure_connected()
    user = input("Choose a username: ")
    pw = input("Choose a password: ")

    cur = db.cursor()
    cur.execute(f"INSERT INTO client(Username, Password) VALUES('{user}','{pw}')")
    db.commit()
    client_menu()


def reconnect_and_go(id):
    ensure_connected()
    print("Connected to 'movie'.")
    admin_menu(id)


def delete_client(id):
    cur = db.cursor()
    cur.execute("SELECT * FROM client")
    data = cur.fetchall()
    print(tabulate.tabulate(data, headers=["ID", "Username", "Password"]))

    target = input("Enter ID to delete: ")
    cur.execute(f"DELETE FROM client WHERE ID={target}")
    db.commit()

    cur.execute("SELECT * FROM client")
    print(tabulate.tabulate(cur.fetchall(), headers=["ID", "Username", "Password"]))
    admin_menu(id)


def add_movie(id):
    while True:
        t = input("Title: ")
        g = input("Genre: ")
        r = float(input("Rating: "))
        rd = input("Release Date (YYYY-MM-DD): ")
        p = int(input("Base Price: "))

        cur = db.cursor()
        cur.execute(f"INSERT INTO movie(Title,Genre,Rating,ReleaseDate,Price) VALUES('{t}','{g}',{r},'{rd}',{p})")
        db.commit()

        if input("Add another? (y/n): ").lower() != 'y':
            break

    admin_menu(id)


def remove_movie(id):
    cur = db.cursor()
    cur.execute("SELECT * FROM movie")
    movies = cur.fetchall()
    print(tabulate.tabulate(movies, headers=["ID","Title","Genre","Rating","Release","Price"]))

    mid = input("Movie ID to delete: ")
    cur.execute(f"DELETE FROM movie WHERE ID={mid}")
    db.commit()

    cur.execute("SELECT * FROM movie")
    print(tabulate.tabulate(cur.fetchall(), headers=["ID","Title","Genre","Rating","Release","Price"]))
    admin_menu(id)


def view_clients(id):
    cur = db.cursor()
    cur.execute("SELECT * FROM client")
    print(tabulate.tabulate(cur.fetchall(), headers=["ID", "Username", "Password"]))
    admin_menu(id)


def view_finances(id):
    total = seats = n = u = up = 0

    with open("booking.csv", "r") as f:
        for row in csv.reader(f):
            amt = int(row[7])
            cnt = int(row[5])
            total += amt
            seats += cnt

            if row[6] == "Normal": n += cnt
            elif row[6] == "Ultra": u += cnt
            elif row[6] == "Ultra Pro": up += cnt

    print(f"""
Total Revenue:           {total}
Total Seats Booked:      {seats}
Normal Seats:            {n}
Ultra Seats:             {u}
Ultra Pro Seats:         {up}
    """)
    admin_menu(id)


def list_movies(return_to=None, client_id=None):
    cur = db.cursor()
    cur.execute("SELECT * FROM movie")
    print(tabulate.tabulate(cur.fetchall(), headers=["ID","Title","Genre","Rating","Release","Price"]))

    if return_to == "admin":
        admin_menu(client_id)
    elif return_to == "client":
        client_logged(client_id)


def book_ticket(cid):
    cur = db.cursor()
    cur.execute("SELECT * FROM movie")
    movies = cur.fetchall()

    list_movies()
    ref = random.randint(1000, 9999)

    movie_id = int(input("Enter Movie ID: "))
    selection = None
    for mv in movies:
        if mv[0] == movie_id:
            selection = mv
            break

    if not selection:
        print("Invalid movie.")
        return client_logged(cid)

    movie_name = selection[1]
    print("Selected:", movie_name)

    while True:
        y = int(input("Year: "))
        m = int(input("Month: "))
        d = int(input("Day: "))
        try:
            chosen = date(y, m, d)
            if chosen > date.today():
                break
            print("Choose a future date.")
        except:
            print("Invalid date.")

    tm = float(input("Time (24h): "))
    while not (0 <= tm < 24):
        tm = float(input("Invalid. Enter valid time: "))

    seats_taken = 0
    with open("booking.csv") as f:
        for row in csv.reader(f):
            if row[2] == movie_name and row[3] == chosen.strftime("%d/%m/%Y") and float(row[4]) == tm:
                seats_taken += int(row[5])

    if seats_taken == 50:
        print("FULL HOUSE! Try another time.")
        return client_logged(cid)

    print("Seats left:", 50 - seats_taken)
    qty = int(input("How many seats?: "))
    while qty <= 0 or qty > 50 - seats_taken:
        qty = int(input("Invalid. Enter again: "))

    print("""
1. Normal
2. Ultra (+50)
3. Ultra Pro (+100)
    """)
    st = int(input("Choose seat type: "))
    while st not in [1,2,3]:
        st = int(input("Try again: "))

    seat_type = ["Normal","Ultra","Ultra Pro"][st-1]
    extra = [0,50,100][st-1]
    total = (selection[5] + extra) * qty

    print("Total price:", total)

    if input("Confirm? (y/n): ").lower() == 'y':
        with open("booking.csv", "a", newline="") as f:
            csv.writer(f).writerow([
                ref, cid, movie_name,
                chosen.strftime("%d/%m/%Y"),
                tm, qty, seat_type, total
            ])
        print("Booking complete.")
    client_logged(cid)


def cancel_booking(cid):
    found = []
    with open("booking.csv") as f:
        for row in csv.reader(f):
            if row[1] == str(cid):
                found.append(row)

    if not found:
        print("No bookings yet.")
        return client_logged(cid)

    for idx, row in enumerate(found, 1):
        print(f"{idx}. Ref: {row[0]}, Movie: {row[2]}, Price: {row[7]}")

    ref = input("Reference ID to cancel: ")

    with open("booking.csv") as old, open("booking_tmp.csv","w",newline="") as new:
        w = csv.writer(new)
        for row in csv.reader(old):
            if row[0] != ref:
                w.writerow(row)

    os.remove("booking.csv")
    os.rename("booking_tmp.csv","booking.csv")

    print("Booking cancelled.")
    client_logged(cid)


def view_booking(cid):
    has = False
    with open("booking.csv") as f:
        for row in csv.reader(f):
            if row[1] == str(cid):
                has = True
                print("Ref:", row[0], "Movie:", row[2], "Price:", row[7])
    if not has:
        print("No purchases found.")
    client_logged(cid)


def admin_menu(id):
    print("""
1. Connect DB
2. View Clients
3. Create Client Table
4. Create Movie Table
5. Add Movie
6. Remove Movie
7. View Movies
8. Create Booking File
9. View Finances
10. Remove Client
11. Back
""")
    ch = int(input("Enter: "))

    if ch == 1: reconnect_and_go(id)
    elif ch == 2: view_clients(id)
    elif ch == 3: create_client_table(id)
    elif ch == 4: create_movie_table()
    elif ch == 5: add_movie(id)
    elif ch == 6: remove_movie(id)
    elif ch == 7: list_movies("admin", id)
    elif ch == 8: create_booking_csv(id)
    elif ch == 9: view_finances(id)
    elif ch == 10: delete_client(id)
    else: main_menu()


def client_logged(cid):
    print("""
1. Purchase Ticket
2. View Movies
3. View Purchases
4. Cancel Ticket
5. Back
""")
    ch = int(input("Enter: "))

    if ch == 1: book_ticket(cid)
    elif ch == 2: list_movies("client", cid)
    elif ch == 3: view_booking(cid)
    elif ch == 4: cancel_booking(cid)
    else: client_menu()


def client_menu():
    print("""
1. Register
2. Login
3. Back
""")
    ch = int(input("Enter: "))

    if ch == 1: register_client()
    elif ch == 2:
        cid = login_client()
        client_logged(cid)
    else:
        main_menu()


def main_menu():
    print("""
1. Purchase Ticket
2. Admin Controls
3. Exit
4. Dry Run
""")
    ch = int(input("Enter: "))

    if ch == 1:
        ensure_connected()
        client_menu()
    elif ch == 2:
        ensure_connected()
        login_admin()
    elif ch == 3:
        quit()
    else:
        dry_start()


main_menu()
