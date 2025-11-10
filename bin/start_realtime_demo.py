#!/usr/bin/env python3
"""
Interactive Real-Time System Demo

Generates telematics data and shows real-time updates.
"""

import time
import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000"
DRIVER_ID = "DRV-0001"

def login():
    """Login and get auth token."""
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/auth/login",
            json={"username": "demo", "password": "demo123"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"⚠️  Could not login: {e}")
    return None

def get_analysis(token, driver_id):
    """Get real-time analysis."""
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(
            f"{API_BASE}/api/v1/realtime/analysis/{driver_id}",
            headers=headers,
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        pass
    return None

def print_analysis(analysis):
    """Print analysis in a nice format."""
    if not analysis:
        return
    
    data = analysis.get('analysis', {})
    pricing = analysis.get('pricing', {})
    
    print("\n" + "="*60)
    print("📊 REAL-TIME ANALYSIS")
    print("="*60)
    
    if data:
        print(f"\n🛡️  Safety Score: {data.get('safety_score', 0):.1f}/100")
        print(f"⚠️  Risk Score: {data.get('risk_score', 0):.1f}/100")
        
        metrics = data.get('behavior_metrics', {})
        if metrics:
            print(f"\n🚗 Current Speed: {metrics.get('current_speed', 0):.1f} mph")
            print(f"📈 Avg Speed: {metrics.get('avg_speed', 0):.1f} mph")
            print(f"⚡ Max Speed: {metrics.get('max_speed', 0):.1f} mph")
            print(f"\n📊 Events:")
            print(f"   • Harsh Braking: {metrics.get('harsh_braking_count', 0)}")
            print(f"   • Speeding: {metrics.get('speeding_count', 0)}")
            print(f"   • Rapid Acceleration: {metrics.get('rapid_accel_count', 0)}")
            print(f"   • Phone Usage: {metrics.get('phone_usage_count', 0)}")
        
        alerts = data.get('safety_alerts', [])
        if alerts:
            print(f"\n🚨 SAFETY ALERTS ({len(alerts)}):")
            for alert in alerts:
                severity_icon = "🔴" if alert.get('severity') == 'high' else "🟡"
                print(f"   {severity_icon} {alert.get('type', 'unknown').upper()}: {alert.get('message', '')}")
        else:
            print(f"\n✅ No safety alerts")
    
    if pricing:
        print(f"\n💰 PRICING:")
        print(f"   Monthly Premium: ${pricing.get('adjusted_premium', 0):.2f}")
        print(f"   Discount: {pricing.get('discount_percent', 0):.1f}%")
        print(f"   Savings: ${pricing.get('savings', 0):.2f}/year")
    
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}\n")

def main():
    print("🚀 Real-Time Telematics System Demo")
    print("="*60)
    print(f"\nDriver ID: {DRIVER_ID}")
    print(f"API: {API_BASE}")
    print("\nGenerating telematics data...")
    print("Open http://localhost:3000/live in your browser to see the Live Dashboard!")
    print("\nPress Ctrl+C to stop\n")
    
    # Login
    token = login()
    if not token:
        print("⚠️  Could not get auth token, continuing without authentication...")
    
    # Import the data generator
    import subprocess
    import os
    
    script_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "backend",
        "scripts",
        "generate_telematics_data.py"
    )
    
    # Start generating data in background
    print("📡 Starting data generation (every 10 seconds)...")
    print("   Watch the Live Dashboard for real-time updates!\n")
    
    try:
        # Generate initial batch
        subprocess.Popen([
            sys.executable, script_path,
            "--driver-id", DRIVER_ID,
            "--events", "50",
            "--lat", "37.7749",
            "--lon", "-122.4194"
        ])
        
        time.sleep(2)
        
        # Monitor and display updates
        for i in range(12):  # 2 minutes of updates
            # Generate more events
            if i % 2 == 0:  # Every 20 seconds
                subprocess.Popen([
                    sys.executable, script_path,
                    "--driver-id", DRIVER_ID,
                    "--events", "10",
                    "--lat", "37.7749",
                    "--lon", "-122.4194"
                ])
            
            # Get and display analysis
            analysis = get_analysis(token, DRIVER_ID)
            if analysis:
                print_analysis(analysis)
            else:
                print(f"⏳ Waiting for data... ({i+1}/12)")
            
            time.sleep(10)
        
        print("\n✅ Demo complete!")
        print("Continue generating data or check the Live Dashboard at http://localhost:3000/live")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped")
        print("The Live Dashboard will continue to show updates as long as data is being generated.")

if __name__ == "__main__":
    main()

