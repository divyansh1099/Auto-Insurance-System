#!/usr/bin/env python3
"""
Event Consumer Startup Script

Starts Kafka event consumers for processing events.

Usage:
    python bin/start_consumer.py risk-scoring
    python bin/start_consumer.py notification
    python bin/start_consumer.py --all
"""

import sys
import os
import argparse
from multiprocessing import Process

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.events.consumers import start_consumer, CONSUMERS


def run_consumer(consumer_name: str):
    """Run a single consumer."""
    print(f"🚀 Starting {consumer_name} consumer...")
    try:
        start_consumer(consumer_name)
    except KeyboardInterrupt:
        print(f"\n✅ {consumer_name} consumer stopped")
    except Exception as e:
        print(f"❌ {consumer_name} consumer error: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Start Kafka event consumers')
    parser.add_argument(
        'consumer',
        nargs='?',
        choices=list(CONSUMERS.keys()) + ['all'],
        help='Consumer to start (or "all" for all consumers)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Start all consumers'
    )
    
    args = parser.parse_args()
    
    if not args.consumer and not args.all:
        parser.print_help()
        sys.exit(1)
    
    print("🔧 Event Consumer Manager\n")
    
    if args.consumer == 'all' or args.all:
        # Start all consumers in separate processes
        print(f"Starting all {len(CONSUMERS)} consumers...\n")
        
        processes = []
        for consumer_name in CONSUMERS.keys():
            p = Process(target=run_consumer, args=(consumer_name,))
            p.start()
            processes.append(p)
            print(f"  ✅ Started {consumer_name} consumer (PID: {p.pid})")
        
        print(f"\n✅ All consumers started. Press Ctrl+C to stop.\n")
        
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("\n🛑 Stopping all consumers...")
            for p in processes:
                p.terminate()
                p.join()
            print("✅ All consumers stopped")
    else:
        # Start single consumer
        run_consumer(args.consumer)


if __name__ == "__main__":
    main()
