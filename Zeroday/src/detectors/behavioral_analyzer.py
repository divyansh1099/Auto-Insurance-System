"""Behavioral analysis module for detecting unusual patterns."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
import re


class BehavioralAnalyzer:
    """Analyze behavioral patterns to detect zero-day attacks."""
    
    def __init__(self, sensitivity=0.8, time_window=300):
        """Initialize behavioral analyzer.
        
        Args:
            sensitivity: Detection sensitivity (0.0 to 1.0)
            time_window: Time window in seconds for pattern analysis
        """
        self.sensitivity = sensitivity
        self.time_window = time_window
        
        # Behavioral patterns to track
        self.request_patterns = defaultdict(lambda: deque())
        self.user_activities = defaultdict(lambda: defaultdict(int))
        self.ip_activities = defaultdict(lambda: defaultdict(int))
        self.command_patterns = defaultdict(int)
        self.sequence_patterns = deque(maxlen=1000)
        
        # Baseline patterns
        self.baseline_patterns = {}
        self.learning_mode = True
        self.learning_samples = 0
        self.min_learning_samples = 100
    
    def analyze_behavior(self, log_entry):
        """Analyze behavior from log entry.
        
        Args:
            log_entry: Dictionary containing log entry data
            
        Returns:
            Tuple of (is_suspicious: bool, confidence: float, details: dict)
        """
        timestamp = log_entry.get('timestamp', datetime.now())
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        
        source_ip = log_entry.get('source_ip', 'unknown')
        user = log_entry.get('user', 'unknown')
        message = str(log_entry.get('message', ''))
        action = log_entry.get('action', 'unknown')
        
        suspicious_indicators = []
        confidence_scores = []
        
        # 1. Check for unusual request frequency
        freq_score = self._check_request_frequency(source_ip, timestamp)
        if freq_score > self.sensitivity:
            suspicious_indicators.append('unusual_request_frequency')
            confidence_scores.append(freq_score)
        
        # 2. Check for unusual command patterns
        cmd_score = self._check_command_patterns(message, source_ip)
        if cmd_score > self.sensitivity:
            suspicious_indicators.append('unusual_command_pattern')
            confidence_scores.append(cmd_score)
        
        # 3. Check for privilege escalation attempts
        priv_score = self._check_privilege_escalation(message, user)
        if priv_score > self.sensitivity:
            suspicious_indicators.append('privilege_escalation_attempt')
            confidence_scores.append(priv_score)
        
        # 4. Check for unusual access patterns
        access_score = self._check_access_patterns(log_entry)
        if access_score > self.sensitivity:
            suspicious_indicators.append('unusual_access_pattern')
            confidence_scores.append(access_score)
        
        # 5. Check for data exfiltration patterns
        exfil_score = self._check_data_exfiltration(message, source_ip)
        if exfil_score > self.sensitivity:
            suspicious_indicators.append('data_exfiltration_pattern')
            confidence_scores.append(exfil_score)
        
        # Update learning mode
        if self.learning_mode:
            self.learning_samples += 1
            if self.learning_samples >= self.min_learning_samples:
                self.learning_mode = False
                self._build_baseline()
        
        # Calculate overall confidence
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0
        is_suspicious = len(suspicious_indicators) > 0 and overall_confidence > self.sensitivity
        
        details = {
            'indicators': suspicious_indicators,
            'confidence_scores': dict(zip(suspicious_indicators, confidence_scores)),
            'overall_confidence': overall_confidence,
            'source_ip': source_ip,
            'user': user,
            'learning_mode': self.learning_mode
        }
        
        # Update activity tracking
        self._update_activity_tracking(log_entry, timestamp)
        
        return is_suspicious, overall_confidence, details
    
    def _check_request_frequency(self, source_ip, timestamp):
        """Check if request frequency is unusual."""
        # Clean old entries
        cutoff_time = timestamp - timedelta(seconds=self.time_window)
        while (self.request_patterns[source_ip] and 
               self.request_patterns[source_ip][0] < cutoff_time):
            self.request_patterns[source_ip].popleft()
        
        # Add current request
        self.request_patterns[source_ip].append(timestamp)
        
        # Calculate frequency
        request_count = len(self.request_patterns[source_ip])
        avg_requests = sum(len(v) for v in self.request_patterns.values()) / max(len(self.request_patterns), 1)
        
        if avg_requests == 0:
            return 0.0
        
        # Score based on deviation from average
        ratio = request_count / max(avg_requests, 1)
        if ratio > 5:  # 5x more than average
            return min(1.0, (ratio - 5) / 10)
        return 0.0
    
    def _check_command_patterns(self, message, source_ip):
        """Check for unusual command patterns."""
        # Suspicious command patterns
        suspicious_patterns = [
            r'rm\s+-rf',
            r'chmod\s+777',
            r'wget\s+.*\|\s*sh',
            r'curl\s+.*\|\s*sh',
            r'base64\s+-d',
            r'eval\s*\(',
            r'exec\s*\(',
            r'\.\.\/\.\.\/',
            r'cat\s+/etc/passwd',
            r'cat\s+/etc/shadow'
        ]
        
        message_lower = message.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, message_lower):
                return 0.9
        
        # Check for unusual command sequences
        if self.command_patterns:
            cmd = message.split()[0] if message.split() else ''
            cmd_freq = self.command_patterns.get(cmd, 0)
            total_cmds = sum(self.command_patterns.values())
            if total_cmds > 0:
                freq_ratio = cmd_freq / total_cmds
                if freq_ratio < 0.01 and cmd:  # Very rare command
                    return 0.7
        
        return 0.0
    
    def _check_privilege_escalation(self, message, user):
        """Check for privilege escalation attempts."""
        escalation_patterns = [
            r'sudo\s+su',
            r'su\s+-',
            r'passwd\s+',
            r'usermod\s+',
            r'chown\s+.*root',
            r'chmod\s+.*4755',
            r'setuid',
            r'setgid'
        ]
        
        message_lower = message.lower()
        for pattern in escalation_patterns:
            if re.search(pattern, message_lower):
                return 0.85
        
        return 0.0
    
    def _check_access_patterns(self, log_entry):
        """Check for unusual access patterns."""
        # Check for access to sensitive files
        sensitive_paths = [
            '/etc/passwd', '/etc/shadow', '/etc/sudoers',
            '/root/', '/var/log/', '/proc/', '/sys/'
        ]
        
        path = log_entry.get('path', '')
        if any(sp in path for sp in sensitive_paths):
            return 0.8
        
        # Check for unusual time access
        timestamp = log_entry.get('timestamp', datetime.now())
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        
        hour = timestamp.hour
        # Unusual hours (2 AM - 5 AM)
        if 2 <= hour <= 5:
            return 0.6
        
        return 0.0
    
    def _check_data_exfiltration(self, message, source_ip):
        """Check for data exfiltration patterns."""
        exfil_patterns = [
            r'nc\s+.*\s+\d+',  # netcat
            r'ncat\s+.*\s+\d+',
            r'ssh\s+.*\s+.*\s+<',
            r'curl\s+.*http',
            r'wget\s+.*http',
            r'base64.*\|',
            r'tar\s+.*\|\s*'
        ]
        
        message_lower = message.lower()
        for pattern in exfil_patterns:
            if re.search(pattern, message_lower):
                return 0.75
        
        return 0.0
    
    def _update_activity_tracking(self, log_entry, timestamp):
        """Update activity tracking for baseline learning."""
        source_ip = log_entry.get('source_ip', 'unknown')
        user = log_entry.get('user', 'unknown')
        action = log_entry.get('action', 'unknown')
        
        self.user_activities[user][action] += 1
        self.ip_activities[source_ip][action] += 1
        
        message = str(log_entry.get('message', ''))
        if message:
            cmd = message.split()[0] if message.split() else ''
            if cmd:
                self.command_patterns[cmd] += 1
    
    def _build_baseline(self):
        """Build baseline patterns from learned data."""
        # Calculate average activities per user/IP
        if self.user_activities:
            avg_user_actions = sum(len(actions) for actions in self.user_activities.values()) / len(self.user_activities)
            self.baseline_patterns['avg_user_actions'] = avg_user_actions
        
        if self.ip_activities:
            avg_ip_actions = sum(len(actions) for actions in self.ip_activities.values()) / len(self.ip_activities)
            self.baseline_patterns['avg_ip_actions'] = avg_ip_actions
    
    def get_stats(self):
        """Get analyzer statistics."""
        return {
            'learning_mode': self.learning_mode,
            'learning_samples': self.learning_samples,
            'unique_users': len(self.user_activities),
            'unique_ips': len(self.ip_activities),
            'command_patterns': len(self.command_patterns),
            'sensitivity': self.sensitivity
        }

