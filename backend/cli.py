"""Small no-frontend CLI for loading a demo scenario and running simulations."""
import argparse
from datetime import datetime, timezone

from .db import connection, initialize_schema
from . import services
from .schemas import ClaimIn, DonorIn, HospitalIn, OrganIn, RecipientIn


def seed_demo():
    initialize_schema()
    with connection() as conn:
        if conn.execute("SELECT 1 FROM hospitals LIMIT 1").fetchone():
            print("Database already contains hospitals; demo seed skipped.")
            return
    h1, h2, h3 = [services.create_hospital(n)["hospital_id"] for n in ("City Hospital", "Metro Hospital", "Life Care Hospital")]
    d1 = services.create_donor("Demo Donor A", "O+")["donor_id"]
    services.create_donor("Demo Donor B", "A+")
    organ = services.create_organ(OrganIn(donor_id=d1, donor_hospital_id=h1, organ_type="Kidney", blood_type="O+", viability_seconds=3600))["organ_id"]
    services.create_recipient(RecipientIn(name="Rahul Demo", organ_type="Kidney", blood_type="A+", urgency_score=8, waiting_days=30, hospital_id=h1))
    services.create_recipient(RecipientIn(name="Aman Demo", organ_type="Kidney", blood_type="B+", urgency_score=9, waiting_days=20, hospital_id=h2))
    services.create_recipient(RecipientIn(name="Rohit Demo", organ_type="Kidney", blood_type="AB+", urgency_score=7, waiting_days=50, hospital_id=h3))
    print(f"Demo data loaded. Sample organ id: {organ}")


def main():
    parser = argparse.ArgumentParser(description="Organ allocation backend commands")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create PostgreSQL tables and indexes")
    commands.add_parser("seed-demo", help="Load small synthetic demo dataset")
    commands.add_parser("deadlock-demo", help="Detect and resolve a controlled wait-for cycle")
    commands.add_parser("deadlines", help="Mark expired available organs as wasted")
    commands.add_parser("recover", help="Replay committed allocation events")
    commands.add_parser("analytics", help="Print simulation metrics")
    args = parser.parse_args()
    if args.command == "init":
        initialize_schema(); print("Schema ready.")
    elif args.command == "seed-demo": seed_demo()
    elif args.command == "deadlock-demo": print(services.deadlock_demo())
    elif args.command == "deadlines": print(services.process_deadlines())
    elif args.command == "recover": print(services.recover_from_event_log())
    elif args.command == "analytics": print(services.analytics())


if __name__ == "__main__":
    main()
