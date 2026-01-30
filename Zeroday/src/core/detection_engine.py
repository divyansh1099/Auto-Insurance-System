"""Main detection engine that coordinates all detection modules."""

from datetime import datetime
from typing import Dict, List, Tuple
import threading
import time

from ..detectors.anomaly_detector import AnomalyDetector
from ..detectors.behavioral_analyzer import BehavioralAnalyzer
from ..detectors.ml_detector import MLDetector
from ..analyzers.log_analyzer import LogAnalyzer
from ..utils.config_loader import ConfigLoader
from ..utils.logger import SystemLogger


class DetectionEngine:
    """Main engine that coordinates all detection modules."""
    
    def __init__(self, config: ConfigLoader = None, logger: SystemLogger = None, alert_system=None):
        """Initialize detection engine.
        
        Args:
            config: Configuration loader instance
            logger: Logger instance
            alert_system: Optional alert system instance
        """
        self.config = config or ConfigLoader()
        if logger is None:
            logger = SystemLogger(
                self.config.get('system', 'log_dir', default='./logs')
            )
        self.logger = logger.get_logger() if hasattr(logger, 'get_logger') else logger
        
        # Store alert system reference
        self.alert_system = alert_system
        
        # Initialize detectors
        self.anomaly_detector = AnomalyDetector(
            threshold=self.config.get('detection', 'anomaly_threshold', default=0.7)
        )
        
        self.behavioral_analyzer = BehavioralAnalyzer(
            sensitivity=self.config.get('detection', 'behavioral_sensitivity', default=0.8)
        )
        
        self.ml_detector = None
        if self.config.get('detection', 'enable_ml_detection', default=True):
            model_path = self.config.get('ml_model', 'model_path', default='models/detection_model.pkl')
            self.ml_detector = MLDetector(model_path=model_path)
        
        # Initialize log analyzer
        log_paths = self.config.get('monitoring', 'log_paths', default=[])
        self.log_analyzer = LogAnalyzer(log_paths=log_paths)
        
        # Detection statistics
        self.stats = {
            'total_analyzed': 0,
            'anomalies_detected': 0,
            'behavioral_threats': 0,
            'ml_threats': 0,
            'alerts_generated': 0,
            'start_time': datetime.now()
        }
        
        # Threading
        self.monitoring = False
        self.monitor_thread = None
    
    def analyze_log_entry(self, log_entry: Dict) -> Tuple[bool, float, Dict]:
        """Analyze a single log entry using all detection methods.
        
        Args:
            log_entry: Parsed log entry dictionary
            
        Returns:
            Tuple of (is_threat: bool, confidence: float, details: dict)
        """
        self.stats['total_analyzed'] += 1
        
        detection_results = {
            'timestamp': datetime.now().isoformat(),
            'log_entry': log_entry,
            'detections': {}
        }
        
        threat_scores = []
        is_threat = False
        max_confidence = 0.0
        
        # 1. Anomaly Detection
        features = self.anomaly_detector.extract_features(log_entry)
        is_anomaly, anomaly_conf, anomaly_details = self.anomaly_detector.detect_anomaly(features)
        self.anomaly_detector.update_baseline(features)
        
        detection_results['detections']['anomaly'] = {
            'detected': is_anomaly,
            'confidence': anomaly_conf,
            'details': anomaly_details
        }
        
        if is_anomaly:
            threat_scores.append(anomaly_conf)
            if anomaly_conf > max_confidence:
                max_confidence = anomaly_conf
        
        # 2. Behavioral Analysis
        is_suspicious, behavior_conf, behavior_details = self.behavioral_analyzer.analyze_behavior(log_entry)
        
        detection_results['detections']['behavioral'] = {
            'detected': is_suspicious,
            'confidence': behavior_conf,
            'details': behavior_details
        }
        
        if is_suspicious:
            self.stats['behavioral_threats'] += 1
            threat_scores.append(behavior_conf)
            if behavior_conf > max_confidence:
                max_confidence = behavior_conf
        
        # 3. ML Detection
        if self.ml_detector:
            ml_attack, ml_conf, ml_details = self.ml_detector.predict(log_entry)
            
            detection_results['detections']['ml'] = {
                'detected': ml_attack,
                'confidence': ml_conf,
                'details': ml_details
            }
            
            if ml_attack:
                self.stats['ml_threats'] += 1
                threat_scores.append(ml_conf)
                if ml_conf > max_confidence:
                    max_confidence = ml_conf
        
        # Determine if overall threat
        min_confidence = self.config.get('detection', 'min_confidence', default=0.75)
        
        # Threat if any detection method flags it with sufficient confidence
        if threat_scores:
            avg_confidence = sum(threat_scores) / len(threat_scores)
            is_threat = max_confidence >= min_confidence or (len(threat_scores) >= 2 and avg_confidence >= min_confidence * 0.8)
        
        if is_threat:
            if is_anomaly:
                self.stats['anomalies_detected'] += 1
            detection_results['threat'] = True
            detection_results['overall_confidence'] = max_confidence
            detection_results['severity'] = self._calculate_severity(max_confidence, threat_scores)
        else:
            detection_results['threat'] = False
            detection_results['overall_confidence'] = max_confidence
        
        return is_threat, max_confidence, detection_results
    
    def _calculate_severity(self, confidence: float, scores: List[float]) -> str:
        """Calculate threat severity level.
        
        Args:
            confidence: Maximum confidence score
            scores: List of all threat scores
            
        Returns:
            Severity level: low, medium, high, critical
        """
        if confidence >= 0.9 or len(scores) >= 3:
            return 'critical'
        elif confidence >= 0.8:
            return 'high'
        elif confidence >= 0.7:
            return 'medium'
        else:
            return 'low'
    
    def start_monitoring(self):
        """Start real-time log monitoring."""
        if self.monitoring:
            self.logger.warning("Monitoring already started")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Started real-time log monitoring")
    
    def stop_monitoring(self):
        """Stop real-time log monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Stopped real-time log monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        check_interval = self.config.get('monitoring', 'check_interval', default=5)
        log_paths = self.config.get('monitoring', 'log_paths', default=[])
        
        while self.monitoring:
            try:
                for log_entry in self.log_analyzer.monitor_logs(log_paths):
                    is_threat, confidence, details = self.analyze_log_entry(log_entry)
                    
                    if is_threat:
                        self._handle_threat(log_entry, confidence, details)
                
                time.sleep(check_interval)
            
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
    
    def _handle_threat(self, log_entry: Dict, confidence: float, details: Dict):
        """Handle detected threat.
        
        Args:
            log_entry: Original log entry
            confidence: Detection confidence
            details: Detection details
        """
        self.stats['alerts_generated'] += 1
        severity = details.get('severity', 'medium')
        
        # Log the threat
        self.logger.warning(
            f"THREAT DETECTED - Severity: {severity}, Confidence: {confidence:.2f}, "
            f"Source: {log_entry.get('source_ip', 'unknown')}, "
            f"Message: {log_entry.get('message', '')[:100]}"
        )
        
        # Trigger alert if alert system is available
        if self.alert_system:
            self.alert_system.send_alert(details, severity)
    
    def get_stats(self) -> Dict:
        """Get detection engine statistics.
        
        Returns:
            Dictionary with statistics
        """
        runtime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'runtime_seconds': runtime,
            'anomaly_detector': self.anomaly_detector.get_stats(),
            'behavioral_analyzer': self.behavioral_analyzer.get_stats(),
            'ml_detector': self.ml_detector.get_stats() if self.ml_detector else None,
            'monitoring_active': self.monitoring
        }
    
    def train_ml_model(self, training_data: List[Dict], labels: List[int] = None):
        """Train the ML detection model.
        
        Args:
            training_data: List of log entries for training
            labels: Optional labels (1 for attack, 0 for normal)
        """
        if self.ml_detector:
            self.logger.info(f"Training ML model on {len(training_data)} samples")
            self.ml_detector.train(training_data, labels)
            self.logger.info("ML model training completed")
        else:
            self.logger.warning("ML detector not enabled")

