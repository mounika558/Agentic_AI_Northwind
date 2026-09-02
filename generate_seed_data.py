import random
import os

import pandas as pd
from faker import Faker
from datetime import datetime


fake = Faker()


# -----------------------------
# Master Data
# -----------------------------

PLANTS = [
    "PLT-PUN",
    "PLT-CHE",
    "PLT-HYD",
    "PLT-COI"
]

CATEGORIES = [
    "Raw Material",
    "Finished Goods",
    "Packaging",
    "Spare Parts",
    "Chemicals"
]

ORDER_STATUSES = [
    "Open",
    "Closed",
    "Cancelled"
]

INVOICE_STATUSES = [
    "Paid",
    "Overdue",
    "Pending"
]

PRIORITIES = [
    "HIGH",
    "MEDIUM",
    "LOW"
]

TEAMS = [
    "Mechanical",
    "Electrical",
    "IT",
    "Production",
    "Quality"
]

REGIONS = [
    "South",
    "North",
    "East",
    "West",
    "Central"
]


# -----------------------------
# Generate Materials
# -----------------------------

def generate_materials():

    materials = []

    for i in range(1, 501):

        mat_id = f"MAT-{i:04d}"

        materials.append({
            "material_id": mat_id,
            "description": fake.catch_phrase(),
            "category": random.choice(CATEGORIES),
            "unit_price": round(random.uniform(100, 5000), 2),
            "stock_qty": random.randint(10, 500),
            "safety_stock": random.randint(20, 100),
            "plant_code": random.choice(PLANTS),
            "created_on": fake.date_time_between(
                start_date="-1y",
                end_date="now"
            )
        })

    return pd.DataFrame(materials)


# -----------------------------
# Generate Customers
# -----------------------------

def generate_customers():

    customers = []

    for i in range(1, 101):

        cust_id = f"C-{i:03d}"

        customers.append({
            "customer_id": cust_id,
            "name": fake.company(),
            "region": random.choice(REGIONS),
            "credit_limit": round(
                random.uniform(10000, 200000),
                2
            ),
            "outstanding_amount": round(
                random.uniform(0, 50000),
                2
            ),
            "created_on": fake.date_time_between(
                start_date="-2y",
                end_date="now"
            )
        })

    return pd.DataFrame(customers)


# -----------------------------
# Generate Sales Orders
# -----------------------------

def generate_sales_orders(materials, customers):

    sales_orders = []

    material_ids = materials["material_id"].tolist()
    customer_ids = customers["customer_id"].tolist()

    for i in range(1, 801):

        order_id = f"SO-{i:04d}"

        material = random.choice(material_ids)
        customer = random.choice(customer_ids)

        sales_orders.append({
            "order_id": order_id,
            "customer_id": customer,
            "material_id": material,
            "qty": random.randint(1, 100),
            "status": random.choice(ORDER_STATUSES),
            "region": random.choice(REGIONS),
            "created_on": fake.date_time_between(
                start_date="-3m",
                end_date="now"
            )
        })

    return pd.DataFrame(sales_orders)


# -----------------------------
# Generate Invoices
# -----------------------------

def generate_invoices(customers):

    invoices = []

    customer_ids = customers["customer_id"].tolist()

    for i in range(1, 401):

        invoice_id = f"INV-{i:04d}"

        customer = random.choice(customer_ids)

        due_date = fake.date_between(
            start_date="-90d",
            end_date="+30d"
        )

        days_overdue = 0

        if due_date < datetime.now().date():
            days_overdue = (
                datetime.now().date() - due_date
            ).days

        invoices.append({
            "invoice_id": invoice_id,
            "customer_id": customer,
            "amount": round(
                random.uniform(1000, 50000),
                2
            ),
            "due_date": due_date,
            "status": random.choice(INVOICE_STATUSES),
            "days_overdue": days_overdue,
            "created_on": fake.date_time_between(
                start_date="-6m",
                end_date="now"
            )
        })

    return pd.DataFrame(invoices)


# -----------------------------
# Generate Tickets
# -----------------------------

def generate_tickets():

    return pd.DataFrame(columns=[
        "ticket_id",
        "equipment_id",
        "material_id",
        "priority",
        "assigned_team",
        "description",
        "status",
        "created_on",
        "created_by_role"
    ])


# -----------------------------
# Generate Audit Log
# -----------------------------

def generate_audit_log():

    return pd.DataFrame(columns=[
        "log_id",
        "ts",
        "user_role",
        "tool_name",
        "params_masked",
        "outcome"
    ])


# -----------------------------
# Main Function
# -----------------------------

def main():

    print("Generating seed data...")

    # Create data folder if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Generate data
    materials_df = generate_materials()

    customers_df = generate_customers()

    sales_orders_df = generate_sales_orders(
        materials_df,
        customers_df
    )

    invoices_df = generate_invoices(
        customers_df
    )

    tickets_df = generate_tickets()

    audit_log_df = generate_audit_log()

    # Save CSV files
    materials_df.to_csv(
        "data/data_materials.csv",
        index=False
    )

    customers_df.to_csv(
        "data/data_customers.csv",
        index=False
    )

    sales_orders_df.to_csv(
        "data/data_sales_orders.csv",
        index=False
    )

    invoices_df.to_csv(
        "data/data_invoices.csv",
        index=False
    )

    tickets_df.to_csv(
        "data/data_tickets.csv",
        index=False
    )

    audit_log_df.to_csv(
        "data/data_audit_log.csv",
        index=False
    )

    # Print summary
    print("Seed data generated successfully!")
    print("Files saved in 'data/' folder")

    print(f"MATERIALS: {len(materials_df)} rows")
    print(f"CUSTOMERS: {len(customers_df)} rows")
    print(f"SALES_ORDERS: {len(sales_orders_df)} rows")
    print(f"INVOICES: {len(invoices_df)} rows")
    print(f"TICKETS: {len(tickets_df)} rows (empty)")
    print(f"AUDIT_LOG: {len(audit_log_df)} rows (empty)")


# -----------------------------
# Entry Point
# -----------------------------

if __name__ == "__main__":
    main()