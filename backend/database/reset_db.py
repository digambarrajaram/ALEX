#!/usr/bin/env python3
"""
Database Reset Script
Drops all tables, recreates schema, and loads seed data
"""

import sys
import os
import argparse
from pathlib import Path
from decimal import Decimal
import subprocess

from src.client import DataAPIClient
from src.models import Database
from src.schemas import UserCreate, AccountCreate, PositionCreate


# -------------------------------------------------------------------
# Force UTF-8 everywhere (Windows-safe)
# -------------------------------------------------------------------
os.environ["PYTHONUTF8"] = "1"
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# -------------------------------------------------------------------
# Subprocess helper (Windows + Linux safe)
# -------------------------------------------------------------------
def run_cmd(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",   # CRITICAL on Windows
    )


# -------------------------------------------------------------------
# Database helpers
# -------------------------------------------------------------------
def drop_all_tables(db: DataAPIClient):
    """Drop all tables in correct order (respecting foreign keys)"""
    print("🗑️  Dropping existing tables...")

    tables_to_drop = [
        'positions',
        'accounts',
        'jobs',
        'instruments',
        'users',
    ]

    for table in tables_to_drop:
        try:
            db.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"   ✅ Dropped {table}")
        except Exception as e:
            print(f"   ⚠️  Error dropping {table}: {e}")

    try:
        db.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
        print("   ✅ Dropped update_updated_at_column function")
    except Exception as e:
        print(f"   ⚠️  Error dropping function: {e}")


def create_test_data(db_models: Database):
    """Create test user with sample portfolio"""
    print("\n👤 Creating test user and portfolio...")

    user_data = UserCreate(
        clerk_user_id='test_user_001',
        display_name='Test User',
        years_until_retirement=25,
        target_retirement_income=Decimal('100000'),
    )

    existing = db_models.users.find_by_clerk_id('test_user_001')
    if existing:
        print("   ℹ️  Test user already exists")
    else:
        validated = user_data.model_dump()
        db_models.users.create_user(
            clerk_user_id=validated['clerk_user_id'],
            display_name=validated['display_name'],
            years_until_retirement=validated['years_until_retirement'],
            target_retirement_income=validated['target_retirement_income'],
        )
        print("   ✅ Created test user")

    accounts = [
        AccountCreate(
            account_name='401(k)',
            account_purpose='Primary retirement savings',
            cash_balance=Decimal('5000'),
            cash_interest=Decimal('0.045'),
        ),
        AccountCreate(
            account_name='Roth IRA',
            account_purpose='Tax-free retirement savings',
            cash_balance=Decimal('1000'),
            cash_interest=Decimal('0.04'),
        ),
        AccountCreate(
            account_name='Taxable Brokerage',
            account_purpose='General investment account',
            cash_balance=Decimal('2500'),
            cash_interest=Decimal('0.035'),
        ),
    ]

    user_accounts = db_models.accounts.find_by_user('test_user_001')

    if user_accounts:
        print(f"   ℹ️  User already has {len(user_accounts)} accounts")
        account_ids = [acc['id'] for acc in user_accounts]
    else:
        account_ids = []
        for acc_data in accounts:
            validated = acc_data.model_dump()
            acc_id = db_models.accounts.create_account(
                'test_user_001',
                account_name=validated['account_name'],
                account_purpose=validated['account_purpose'],
                cash_balance=validated['cash_balance'],
                cash_interest=validated['cash_interest'],
            )
            account_ids.append(acc_id)
            print(f"   ✅ Created account: {validated['account_name']}")

    if account_ids:
        positions = [
            ('SPY', Decimal('100')),
            ('QQQ', Decimal('50')),
            ('BND', Decimal('200')),
            ('VEA', Decimal('150')),
            ('GLD', Decimal('25')),
        ]

        account_id = account_ids[0]
        existing_positions = db_models.positions.find_by_account(account_id)

        if existing_positions:
            print(f"   ℹ️  Account already has {len(existing_positions)} positions")
        else:
            for symbol, quantity in positions:
                position = PositionCreate(
                    account_id=account_id,
                    symbol=symbol,
                    quantity=quantity,
                )
                validated = position.model_dump()
                db_models.positions.add_position(
                    validated['account_id'],
                    validated['symbol'],
                    validated['quantity'],
                )
                print(f"   ✅ Added position: {quantity} shares of {symbol}")


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Reset Alex database')
    parser.add_argument('--with-test-data', action='store_true',
                        help='Create test user with sample portfolio')
    parser.add_argument('--skip-drop', action='store_true',
                        help='Skip dropping tables (just reload data)')
    args = parser.parse_args()

    print("🚀 Database Reset Script")
    print("=" * 50)

    db = DataAPIClient()
    db_models = Database()

    if not args.skip_drop:
        drop_all_tables(db)

        print("\n📝 Running migrations...")
        result = run_cmd(['uv', 'run', 'run_migrations.py'])

        if result.returncode != 0:
            print("❌ Migration failed!")
            print(result.stderr or "")
            sys.exit(1)
        else:
            print("✅ Migrations completed")

    print("\n🌱 Loading seed data...")
    result = run_cmd(['uv', 'run', 'seed_data.py'])

    if result.returncode != 0:
        print("❌ Seed data failed!")
        print(result.stderr or "")
        sys.exit(1)
    else:
        stdout = result.stdout or ""
        if '22/22 instruments loaded' in stdout:
            print("✅ Loaded 22 instruments")
        else:
            print("✅ Seed data loaded")

    if args.with_test_data:
        create_test_data(db_models)

    print("\n🔍 Final verification...")
    tables = ['users', 'instruments', 'accounts', 'positions', 'jobs']
    for table in tables:
        result = db.query(f"SELECT COUNT(*) as count FROM {table}")
        count = result[0]['count'] if result else 0
        print(f"   • {table}: {count} records")

    print("\n" + "=" * 50)
    print("✅ Database reset complete!")

    if args.with_test_data:
        print("\n📝 Test user created:")
        print("   • User ID: test_user_001")
        print("   • 3 accounts (401k, Roth IRA, Taxable)")
        print("   • 5 positions in 401k account")


if __name__ == "__main__":
    main()
