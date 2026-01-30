#!/usr/bin/env python3
"""
Zero-Day Attack Detection System
Main entry point for the detection system.
"""

import sys
import argparse
import signal
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.detection_engine import DetectionEngine
from src.core.alert_system import AlertSystem
from src.utils.config_loader import ConfigLoader
from src.utils.logger import SystemLogger
from src.analyzers.log_analyzer import LogAnalyzer


class ZeroDayDetectionSystem:
    """Main application class for zero-day attack detection."""
    
    def __init__(self, config_path="config.yaml"):
        """Initialize the detection system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigLoader(config_path)
        self.logger_instance = SystemLogger(
            log_dir=self.config.get('system', 'log_dir', default='./logs')
        )
        self.logger = self.logger_instance.get_logger()
        
        self.alert_system = AlertSystem(config=self.config, logger=self.logger_instance)
        self.detection_engine = DetectionEngine(
            config=self.config, 
            logger=self.logger_instance,
            alert_system=self.alert_system
        )
        
        self.running = False
    
    def start(self):
        """Start the detection system."""
        self.logger.info("Starting Zero-Day Attack Detection System")
        self.logger.info(f"Configuration loaded from: {self.config.config_path}")
        
        # Check if monitoring is enabled
        if self.config.get('monitoring', 'real_time', default=True):
            self.detection_engine.start_monitoring()
            self.running = True
            self.logger.info("Real-time monitoring started")
        else:
            self.logger.info("Real-time monitoring disabled in config")
    
    def stop(self):
        """Stop the detection system."""
        self.logger.info("Stopping Zero-Day Attack Detection System")
        self.detection_engine.stop_monitoring()
        self.running = False
        
        # Generate final report
        self.alert_system.generate_report()
        
        # Print statistics
        stats = self.detection_engine.get_stats()
        self.logger.info("=" * 60)
        self.logger.info("Detection Statistics:")
        self.logger.info(f"  Total Analyzed: {stats['total_analyzed']}")
        self.logger.info(f"  Anomalies Detected: {stats['anomalies_detected']}")
        self.logger.info(f"  Behavioral Threats: {stats['behavioral_threats']}")
        self.logger.info(f"  ML Threats: {stats['ml_threats']}")
        self.logger.info(f"  Alerts Generated: {stats['alerts_generated']}")
        self.logger.info(f"  Runtime: {stats['runtime_seconds']:.2f} seconds")
        self.logger.info("=" * 60)
    
    def analyze_file(self, file_path: str):
        """Analyze a single log file.
        
        Args:
            file_path: Path to log file
        """
        self.logger.info(f"Analyzing log file: {file_path}")
        
        log_analyzer = LogAnalyzer()
        threat_count = 0
        
        for log_entry in log_analyzer.read_log_file(file_path):
            is_threat, confidence, details = self.detection_engine.analyze_log_entry(log_entry)
            
            if is_threat:
                threat_count += 1
                severity = details.get('severity', 'medium')
                self.alert_system.send_alert(details, severity)
        
        self.logger.info(f"Analysis complete. Threats detected: {threat_count}")
    
    def train_model(self, training_file: str, labels_file: str = None):
        """Train the ML detection model.
        
        Args:
            training_file: Path to training data file (JSON lines)
            labels_file: Optional path to labels file
        """
        self.logger.info(f"Training ML model with data from: {training_file}")
        
        import json
        training_data = []
        labels = None
        
        # Load training data
        with open(training_file, 'r') as f:
            for line in f:
                if line.strip():
                    training_data.append(json.loads(line))
        
        # Load labels if provided
        if labels_file:
            with open(labels_file, 'r') as f:
                labels = [int(line.strip()) for line in f]
        
        self.detection_engine.train_ml_model(training_data, labels)
        self.logger.info("Model training completed")
    
    def run_interactive(self):
        """Run in interactive mode."""
        self.logger.info("Running in interactive mode. Type 'help' for commands.")
        
        commands = {
            'help': self._print_help,
            'stats': self._show_stats,
            'alerts': self._show_alerts,
            'report': self._generate_report,
            'quit': lambda: None
        }
        
        while self.running:
            try:
                command = input("\n> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command in commands:
                    commands[command]()
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in interactive mode: {e}")
    
    def _print_help(self):
        """Print help message."""
        print("""
Available commands:
  help    - Show this help message
  stats   - Show detection statistics
  alerts  - Show recent alerts
  report  - Generate alert report
  quit    - Exit the system
        """)
    
    def _show_stats(self):
        """Show detection statistics."""
        stats = self.detection_engine.get_stats()
        print("\nDetection Statistics:")
        print(f"  Total Analyzed: {stats['total_analyzed']}")
        print(f"  Anomalies Detected: {stats['anomalies_detected']}")
        print(f"  Behavioral Threats: {stats['behavioral_threats']}")
        print(f"  ML Threats: {stats['ml_threats']}")
        print(f"  Alerts Generated: {stats['alerts_generated']}")
        print(f"  Runtime: {stats['runtime_seconds']:.2f} seconds")
    
    def _show_alerts(self):
        """Show recent alerts."""
        alerts = self.alert_system.get_recent_alerts(limit=10)
        print(f"\nRecent Alerts ({len(alerts)}):")
        for i, alert in enumerate(alerts, 1):
            details = alert['details']
            log_entry = details.get('log_entry', {})
            print(f"\n{i}. [{alert['severity'].upper()}] {alert['timestamp']}")
            print(f"   Source: {log_entry.get('source_ip', 'unknown')}")
            print(f"   Confidence: {details.get('overall_confidence', 0.0):.2%}")
            print(f"   Message: {log_entry.get('message', '')[:80]}")
    
    def _generate_report(self):
        """Generate alert report."""
        report = self.alert_system.generate_report()
        print("\n" + report)


def signal_handler(sig, frame):
    """Handle interrupt signals."""
    print("\nReceived interrupt signal. Shutting down...")
    if 'system' in globals():
        system.stop()
    sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Zero-Day Attack Detection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start real-time monitoring
  python main.py --monitor

  # Analyze a log file
  python main.py --analyze /var/log/auth.log

  # Train ML model
  python main.py --train training_data.jsonl --labels labels.txt

  # Interactive mode
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--monitor', '-m',
        action='store_true',
        help='Start real-time log monitoring'
    )
    
    parser.add_argument(
        '--analyze', '-a',
        metavar='FILE',
        help='Analyze a single log file'
    )
    
    parser.add_argument(
        '--train',
        metavar='FILE',
        help='Train ML model with training data file'
    )
    
    parser.add_argument(
        '--labels',
        metavar='FILE',
        help='Labels file for supervised training'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize system
    global system
    system = ZeroDayDetectionSystem(config_path=args.config)
    
    try:
        if args.train:
            # Training mode
            system.train_model(args.train, args.labels)
        
        elif args.analyze:
            # File analysis mode
            system.analyze_file(args.analyze)
            system.stop()
        
        elif args.monitor or args.interactive:
            # Monitoring or interactive mode
            system.start()
            
            if args.interactive:
                system.run_interactive()
            else:
                # Keep running until interrupted
                try:
                    while system.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            
            system.stop()
        
        else:
            # Default: show help
            parser.print_help()
    
    except Exception as e:
        system.logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

