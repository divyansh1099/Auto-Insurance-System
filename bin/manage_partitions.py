#!/usr/bin/env python3
"""
Partition Management Script for telematics_events

Manages monthly partitions for the telematics_events table.

Usage:
    python bin/manage_partitions.py create --months 6
    python bin/manage_partitions.py list
    python bin/manage_partitions.py drop --partition telematics_events_2023_01
    python bin/manage_partitions.py archive --before 2024-01-01
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.models.database import SessionLocal


def create_partitions(months_ahead: int = 3):
    """Create partitions for future months."""
    db = SessionLocal()
    
    try:
        print(f"🔧 Creating partitions for next {months_ahead} months...")
        
        current_date = datetime.now().replace(day=1)
        
        for i in range(1, months_ahead + 1):
            partition_date = current_date + relativedelta(months=i)
            partition_name = f"telematics_events_{partition_date.strftime('%Y_%m')}"
            start_date = partition_date
            end_date = start_date + relativedelta(months=1)
            
            # Check if partition exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = :partition_name
                )
            """)
            
            exists = db.execute(check_query, {"partition_name": partition_name}).scalar()
            
            if exists:
                print(f"  ⏭️  {partition_name} already exists")
                continue
            
            # Create partition
            create_query = text(f"""
                CREATE TABLE {partition_name} PARTITION OF telematics_events
                FOR VALUES FROM ('{start_date.strftime('%Y-%m-%d')}') 
                TO ('{end_date.strftime('%Y-%m-%d')}')
            """)
            
            db.execute(create_query)
            db.commit()
            
            print(f"  ✅ Created {partition_name} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
        
        print(f"\n✅ Partition creation complete!")
        
    except Exception as e:
        print(f"❌ Error creating partitions: {str(e)}")
        db.rollback()
    finally:
        db.close()


def list_partitions():
    """List all existing partitions with sizes."""
    db = SessionLocal()
    
    try:
        print("📊 Listing all telematics_events partitions...\n")
        
        query = text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
            FROM pg_tables
            WHERE tablename LIKE 'telematics_events_%'
            ORDER BY tablename
        """)
        
        results = db.execute(query).fetchall()
        
        if not results:
            print("No partitions found.")
            return
        
        print(f"{'Partition Name':<35} {'Size':<15}")
        print("=" * 50)
        
        total_size = 0
        for row in results:
            print(f"{row.tablename:<35} {row.size:<15}")
            total_size += row.size_bytes
        
        print("=" * 50)
        print(f"{'Total':<35} {format_bytes(total_size):<15}")
        print(f"\nTotal partitions: {len(results)}")
        
    except Exception as e:
        print(f"❌ Error listing partitions: {str(e)}")
    finally:
        db.close()


def drop_partition(partition_name: str):
    """Drop a specific partition."""
    db = SessionLocal()
    
    try:
        # Confirm
        response = input(f"⚠️  Are you sure you want to drop partition '{partition_name}'? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        print(f"🗑️  Dropping partition {partition_name}...")
        
        # Check if partition exists
        check_query = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_class WHERE relname = :partition_name
            )
        """)
        
        exists = db.execute(check_query, {"partition_name": partition_name}).scalar()
        
        if not exists:
            print(f"❌ Partition {partition_name} does not exist")
            return
        
        # Drop partition
        drop_query = text(f"DROP TABLE {partition_name}")
        db.execute(drop_query)
        db.commit()
        
        print(f"✅ Partition {partition_name} dropped successfully")
        
    except Exception as e:
        print(f"❌ Error dropping partition: {str(e)}")
        db.rollback()
    finally:
        db.close()


def archive_old_partitions(before_date: str):
    """Archive (export and drop) partitions before a certain date."""
    db = SessionLocal()
    
    try:
        before = datetime.strptime(before_date, '%Y-%m-%d')
        print(f"📦 Archiving partitions before {before_date}...")
        
        # Get partitions to archive
        query = text("""
            SELECT tablename
            FROM pg_tables
            WHERE tablename LIKE 'telematics_events_%'
            ORDER BY tablename
        """)
        
        results = db.execute(query).fetchall()
        
        archived_count = 0
        for row in results:
            partition_name = row.tablename
            
            # Extract date from partition name (format: telematics_events_YYYY_MM)
            try:
                parts = partition_name.split('_')
                year = int(parts[2])
                month = int(parts[3])
                partition_date = datetime(year, month, 1)
                
                if partition_date < before:
                    # Export to CSV (optional - you can implement this)
                    export_path = f"/tmp/{partition_name}.csv"
                    print(f"  📤 Exporting {partition_name} to {export_path}...")
                    
                    export_query = text(f"""
                        COPY (SELECT * FROM {partition_name}) 
                        TO '{export_path}' 
                        WITH CSV HEADER
                    """)
                    
                    try:
                        db.execute(export_query)
                        print(f"  ✅ Exported {partition_name}")
                    except Exception as e:
                        print(f"  ⚠️  Export failed (may need superuser): {str(e)}")
                    
                    # Drop partition
                    response = input(f"  Drop {partition_name}? (yes/no): ")
                    if response.lower() == 'yes':
                        drop_query = text(f"DROP TABLE {partition_name}")
                        db.execute(drop_query)
                        db.commit()
                        print(f"  🗑️  Dropped {partition_name}")
                        archived_count += 1
                    
            except (IndexError, ValueError):
                print(f"  ⚠️  Skipping {partition_name} (invalid format)")
                continue
        
        print(f"\n✅ Archived {archived_count} partitions")
        
    except Exception as e:
        print(f"❌ Error archiving partitions: {str(e)}")
        db.rollback()
    finally:
        db.close()


def format_bytes(bytes_value):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def main():
    parser = argparse.ArgumentParser(description='Manage telematics_events partitions')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create future partitions')
    create_parser.add_argument('--months', type=int, default=3, help='Number of months ahead (default: 3)')
    
    # List command
    subparsers.add_parser('list', help='List all partitions')
    
    # Drop command
    drop_parser = subparsers.add_parser('drop', help='Drop a specific partition')
    drop_parser.add_argument('--partition', required=True, help='Partition name to drop')
    
    # Archive command
    archive_parser = subparsers.add_parser('archive', help='Archive old partitions')
    archive_parser.add_argument('--before', required=True, help='Archive partitions before this date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print("🔧 Telematics Events Partition Manager\n")
    
    if args.command == 'create':
        create_partitions(args.months)
    elif args.command == 'list':
        list_partitions()
    elif args.command == 'drop':
        drop_partition(args.partition)
    elif args.command == 'archive':
        archive_old_partitions(args.before)


if __name__ == "__main__":
    main()
