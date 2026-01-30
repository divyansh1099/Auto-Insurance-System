"""Anomaly detection module using statistical methods."""

import numpy as np
from collections import deque
from datetime import datetime, timedelta
import statistics


class AnomalyDetector:
    """Detect anomalies using statistical analysis and baseline comparison."""
    
    def __init__(self, threshold=0.7, window_size=1000):
        """Initialize anomaly detector.
        
        Args:
            threshold: Anomaly detection threshold (0.0 to 1.0)
            window_size: Size of sliding window for baseline calculation
        """
        self.threshold = threshold
        self.window_size = window_size
        self.baseline_data = deque(maxlen=window_size)
        self.feature_stats = {}
        self.anomaly_count = 0
    
    def update_baseline(self, features):
        """Update baseline statistics with new data.
        
        Args:
            features: Dictionary of feature values
        """
        self.baseline_data.append(features)
        
        # Update statistics for each feature
        if len(self.baseline_data) > 10:  # Need minimum data for stats
            for feature_name in features.keys():
                values = [d.get(feature_name, 0) for d in self.baseline_data 
                         if isinstance(d.get(feature_name), (int, float))]
                
                if values:
                    self.feature_stats[feature_name] = {
                        'mean': statistics.mean(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values)
                    }
    
    def detect_anomaly(self, features):
        """Detect if features represent an anomaly.
        
        Args:
            features: Dictionary of feature values to analyze
            
        Returns:
            Tuple of (is_anomaly: bool, confidence: float, details: dict)
        """
        if len(self.baseline_data) < 10:
            # Not enough baseline data yet
            self.update_baseline(features)
            return False, 0.0, {'reason': 'Insufficient baseline data'}
        
        anomaly_scores = {}
        total_score = 0.0
        feature_count = 0
        
        for feature_name, value in features.items():
            if not isinstance(value, (int, float)):
                continue
                
            if feature_name not in self.feature_stats:
                continue
            
            stats = self.feature_stats[feature_name]
            mean = stats['mean']
            std = stats['std']
            
            if std == 0:
                # No variance, check if value differs from mean
                score = 1.0 if value != mean else 0.0
            else:
                # Calculate z-score
                z_score = abs((value - mean) / std)
                # Convert z-score to anomaly score (0-1)
                score = min(1.0, z_score / 3.0)  # 3 sigma rule
            
            anomaly_scores[feature_name] = score
            total_score += score
            feature_count += 1
        
        if feature_count == 0:
            return False, 0.0, {'reason': 'No numeric features to analyze'}
        
        avg_score = total_score / feature_count
        is_anomaly = avg_score >= self.threshold
        
        if is_anomaly:
            self.anomaly_count += 1
        
        details = {
            'anomaly_score': avg_score,
            'feature_scores': anomaly_scores,
            'threshold': self.threshold,
            'baseline_size': len(self.baseline_data)
        }
        
        return is_anomaly, avg_score, details
    
    def extract_features(self, log_entry):
        """Extract features from log entry for anomaly detection.
        
        Args:
            log_entry: Dictionary containing log entry data
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            'timestamp': log_entry.get('timestamp', 0),
            'length': len(str(log_entry.get('message', ''))),
            'word_count': len(str(log_entry.get('message', '')).split()),
            'special_chars': sum(1 for c in str(log_entry.get('message', '')) 
                               if not c.isalnum() and not c.isspace()),
            'numeric_count': sum(1 for c in str(log_entry.get('message', '')) 
                               if c.isdigit()),
        }
        
        # Add source-specific features
        if 'source_ip' in log_entry:
            ip = log_entry['source_ip']
            features['ip_octet_1'] = int(ip.split('.')[0]) if '.' in ip else 0
        
        if 'status_code' in log_entry:
            features['status_code'] = int(log_entry['status_code'])
        
        if 'response_time' in log_entry:
            features['response_time'] = float(log_entry['response_time'])
        
        return features
    
    def get_stats(self):
        """Get detector statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            'baseline_size': len(self.baseline_data),
            'anomaly_count': self.anomaly_count,
            'threshold': self.threshold,
            'feature_count': len(self.feature_stats)
        }

