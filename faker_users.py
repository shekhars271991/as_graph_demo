import json
import random
import argparse
from faker import Faker
from datetime import datetime, timedelta

# Setup
fake = Faker("en_IN")
Faker.seed(42)
random.seed(42)

# Command-line argument
parser = argparse.ArgumentParser(description="Generate Indian user data with optional fraud flag")
parser.add_argument("-f", "--fraud", action="store_true", help="Mark all accounts as fraudFlag: true")
args = parser.parse_args()

# Config
NUM_USERS = 200
START_DATE = datetime(2023, 1, 1)
occupations = [
    "Software Engineer", "Teacher", "Accountant", "Sales Representative",
    "Marketing Manager", "Nurse", "Police Officer", "Data Scientist",
    "HR Specialist", "Web Developer", "Graphic Designer", "Financial Analyst",
    "Project Manager", "Real Estate Agent", "Construction Manager"
]
cities = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata",
    "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal"
]

users = []

# Generate users
for i in range(NUM_USERS):
    user_id = f"U{str(i+1).zfill(4)}"
    name = fake.name()
    email = fake.email()
    age = random.randint(22, 60)
    location = random.choice(cities)
    occupation = random.choice(occupations)
    risk_score = round(random.uniform(5.0, 35.0), 1)
    signup_date = START_DATE + timedelta(days=random.randint(0, 600), minutes=random.randint(0, 1440))
    phone = fake.phone_number()

    accounts = []

    # Default account: savings
    account_savings = {
        "id": f"A{str(i*2+1).zfill(5)}",
        "type": "savings",
        "balance": round(random.uniform(3000.0, 500000.0), 2),
        "created_date": signup_date.isoformat() + "Z"
    }
    if args.fraud:
        account_savings["fraudFlag"] = True
    accounts.append(account_savings)

    # Optional credit account
    if random.random() < 0.5:
        account_credit = {
            "id": f"A{str(i*2+2).zfill(5)}",
            "type": "credit",
            "balance": round(random.uniform(5000.0, 100000.0), 2) * -1,
            "created_date": signup_date.isoformat() + "Z"
        }
        if args.fraud:
            account_credit["fraudFlag"] = True
        accounts.append(account_credit)

    users.append({
        "id": user_id,
        "name": name,
        "email": email,
        "age": age,
        "location": location,
        "occupation": occupation,
        "risk_score": risk_score,
        "signup_date": signup_date.isoformat() + "Z",
        "phone": phone,
        "accounts": accounts
    })

# Save to JSON
filename = f"users_{NUM_USERS}_india_fraud.json" if args.fraud else  f"users_{NUM_USERS}_india.json"
with open(filename, "w") as f:
    json.dump({"users": users}, f, indent=2)

print(f"✅ Generated {NUM_USERS} Indian users with accounts in {filename}")
