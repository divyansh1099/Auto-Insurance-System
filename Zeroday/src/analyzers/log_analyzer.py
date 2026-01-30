"""Log file analyzer for processing and parsing log entries."""

import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Iterator
import json


class LogAnalyzer:
    """Analyze and parse various log file formats."""
    
    # Common log patterns
    LOG_PATTERNS = {
        'syslog': r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.+)',
        'auth': r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.+)',
        'nginx': r'(\S+)\s+-\s+-\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)\s+"([^"]+)"\s+"([^"]+)"',
        'apache': r'(\S+)\s+(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)',
        'json': None  # JSON logs are handled separately
    }
    
    def __init__(self, log_paths: List[str] = None):
        """Initialize log analyzer.
        
        Args:
            log_paths: List of log file paths to monitor
        """
        self.log_paths = log_paths or []
        self.file_positions = {}  # Track reading position for each file
        self.last_modified = {}
    
    def detect_log_format(self, line: str) -> str:
        """Detect log format from a line.
        
        Args:
            line: Log line to analyze
            
        Returns:
            Detected log format name
        """
        # Check for JSON
        try:
            json.loads(line)
            return 'json'
        except:
            pass
        
        # Check for nginx format
        if re.match(self.LOG_PATTERNS['nginx'], line):
            return 'nginx'
        
        # Check for apache format
        if re.match(self.LOG_PATTERNS['apache'], line):
            return 'apache'
        
        # Check for syslog/auth format
        if re.match(self.LOG_PATTERNS['syslog'], line):
            return 'syslog'
        
        return 'unknown'
    
    def parse_log_line(self, line: str, log_format: str = None) -> Dict:
        """Parse a log line into structured format.
        
        Args:
            line: Log line to parse
            log_format: Log format (auto-detected if None)
            
        Returns:
            Dictionary with parsed log data
        """
        if not line.strip():
            return None
        
        if log_format is None:
            log_format = self.detect_log_format(line)
        
        parsed = {
            'raw': line,
            'format': log_format,
            'timestamp': datetime.now().timestamp(),
            'message': line,
            'source_ip': 'unknown',
            'user': 'unknown',
            'action': 'unknown'
        }
        
        try:
            if log_format == 'json':
                data = json.loads(line)
                parsed.update(data)
                if 'timestamp' in data:
                    parsed['timestamp'] = self._parse_timestamp(data['timestamp'])
            
            elif log_format == 'nginx':
                match = re.match(self.LOG_PATTERNS['nginx'], line)
                if match:
                    parsed['source_ip'] = match.group(1)
                    parsed['timestamp'] = self._parse_timestamp(match.group(2))
                    request = match.group(3)
                    parsed['status_code'] = match.group(4)
                    parsed['response_size'] = match.group(5)
                    parsed['message'] = request
                    parsed['action'] = request.split()[0] if request.split() else 'unknown'
            
            elif log_format == 'apache':
                match = re.match(self.LOG_PATTERNS['apache'], line)
                if match:
                    parsed['source_ip'] = match.group(1)
                    parsed['timestamp'] = self._parse_timestamp(match.group(4))
                    request = match.group(5)
                    parsed['status_code'] = match.group(6)
                    parsed['response_size'] = match.group(7)
                    parsed['message'] = request
                    parsed['action'] = request.split()[0] if request.split() else 'unknown'
            
            elif log_format == 'syslog' or log_format == 'auth':
                match = re.match(self.LOG_PATTERNS['syslog'], line)
                if match:
                    parsed['timestamp'] = self._parse_timestamp(match.group(1))
                    parsed['hostname'] = match.group(2)
                    message = match.group(3)
                    parsed['message'] = message
                    
                    # Try to extract user and IP from message
                    user_match = re.search(r'user=(\S+)', message)
                    if user_match:
                        parsed['user'] = user_match.group(1)
                    
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', message)
                    if ip_match:
                        parsed['source_ip'] = ip_match.group(1)
                    
                    # Extract action
                    action_match = re.search(r'(\w+):', message)
                    if action_match:
                        parsed['action'] = action_match.group(1)
        
        except Exception as e:
            parsed['parse_error'] = str(e)
        
        return parsed
    
    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Parse timestamp string to Unix timestamp.
        
        Args:
            timestamp_str: Timestamp string in various formats
            
        Returns:
            Unix timestamp (float)
        """
        # Common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%b %d %H:%M:%S',
            '%d/%b/%Y:%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                # Adjust year if not specified (assume current year)
                if dt.year == 1900:
                    dt = dt.replace(year=datetime.now().year)
                return dt.timestamp()
            except:
                continue
        
        return datetime.now().timestamp()
    
    def read_log_file(self, file_path: str, from_position: int = 0) -> Iterator[Dict]:
        """Read log file and yield parsed entries.
        
        Args:
            file_path: Path to log file
            from_position: Byte position to start reading from
            
        Yields:
            Parsed log entry dictionaries
        """
        if not os.path.exists(file_path):
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(from_position)
                for line in f:
                    parsed = self.parse_log_line(line.strip())
                    if parsed:
                        yield parsed
        except Exception as e:
            print(f"Error reading log file {file_path}: {e}")
    
    def get_new_entries(self, file_path: str) -> List[Dict]:
        """Get new log entries since last read.
        
        Args:
            file_path: Path to log file
            
        Returns:
            List of new parsed log entries
        """
        if file_path not in self.file_positions:
            self.file_positions[file_path] = 0
        
        entries = []
        current_position = self.file_positions[file_path]
        
        try:
            file_size = os.path.getsize(file_path)
            
            # If file was truncated, reset position
            if file_size < current_position:
                current_position = 0
            
            for entry in self.read_log_file(file_path, current_position):
                entries.append(entry)
            
            # Update position
            self.file_positions[file_path] = file_size
            
        except Exception as e:
            print(f"Error getting new entries from {file_path}: {e}")
        
        return entries
    
    def monitor_logs(self, log_paths: List[str] = None) -> Iterator[Dict]:
        """Monitor multiple log files and yield new entries.
        
        Args:
            log_paths: List of log file paths (uses self.log_paths if None)
            
        Yields:
            Parsed log entries with 'source_file' field added
        """
        paths = log_paths or self.log_paths
        
        for log_path in paths:
            if not os.path.exists(log_path):
                continue
            
            for entry in self.get_new_entries(log_path):
                entry['source_file'] = log_path
                yield entry
    
    def get_file_stats(self, file_path: str) -> Dict:
        """Get statistics about a log file.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Dictionary with file statistics
        """
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        return {
            'path': file_path,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'position': self.file_positions.get(file_path, 0)
        }

