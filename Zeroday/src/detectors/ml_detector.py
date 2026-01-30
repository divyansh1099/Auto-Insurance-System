"""Machine Learning-based detection module."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os
from pathlib import Path


class MLDetector:
    """Machine Learning-based zero-day attack detector."""
    
    def __init__(self, model_path="models/detection_model.pkl", retrain_interval=7):
        """Initialize ML detector.
        
        Args:
            model_path: Path to save/load ML model
            retrain_interval: Days between retraining
        """
        self.model_path = Path(model_path)
        self.retrain_interval = retrain_interval
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if exists."""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.scaler = model_data['scaler']
                    self.feature_names = model_data.get('feature_names', [])
                    self.is_trained = True
            except Exception as e:
                print(f"Error loading model: {e}")
                self._initialize_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize new model."""
        # Use Isolation Forest for anomaly detection
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.is_trained = False
    
    def extract_features(self, log_entry):
        """Extract features from log entry for ML model.
        
        Args:
            log_entry: Dictionary containing log entry data
            
        Returns:
            Dictionary of extracted features
        """
        message = str(log_entry.get('message', ''))
        source_ip = log_entry.get('source_ip', 'unknown')
        user = log_entry.get('user', 'unknown')
        
        features = {
            # Text features
            'message_length': len(message),
            'word_count': len(message.split()),
            'char_diversity': len(set(message)) / max(len(message), 1),
            'special_char_ratio': sum(1 for c in message if not c.isalnum() and not c.isspace()) / max(len(message), 1),
            'numeric_ratio': sum(1 for c in message if c.isdigit()) / max(len(message), 1),
            'uppercase_ratio': sum(1 for c in message if c.isupper()) / max(len(message), 1),
            'url_count': message.count('http') + message.count('www'),
            'ip_count': len([x for x in message.split() if '.' in x and x.replace('.', '').isdigit()]),
            
            # Pattern features
            'has_sudo': 1 if 'sudo' in message.lower() else 0,
            'has_su': 1 if ' su ' in message.lower() or message.lower().startswith('su ') else 0,
            'has_rm': 1 if 'rm ' in message.lower() else 0,
            'has_chmod': 1 if 'chmod' in message.lower() else 0,
            'has_wget': 1 if 'wget' in message.lower() else 0,
            'has_curl': 1 if 'curl' in message.lower() else 0,
            'has_pipe': 1 if '|' in message else 0,
            'has_redirect': 1 if '>' in message or '>>' in message else 0,
            'has_background': 1 if '&' in message else 0,
            
            # Source features
            'ip_known': 1 if source_ip != 'unknown' else 0,
            'user_known': 1 if user != 'unknown' else 0,
        }
        
        # Add status code if available
        if 'status_code' in log_entry:
            features['status_code'] = int(log_entry['status_code'])
        else:
            features['status_code'] = 0
        
        # Add response time if available
        if 'response_time' in log_entry:
            features['response_time'] = float(log_entry['response_time'])
        else:
            features['response_time'] = 0.0
        
        # Add timestamp features
        timestamp = log_entry.get('timestamp', 0)
        if isinstance(timestamp, (int, float)):
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
            features['hour'] = dt.hour
            features['day_of_week'] = dt.weekday()
        else:
            features['hour'] = 0
            features['day_of_week'] = 0
        
        return features
    
    def train(self, training_data, labels=None):
        """Train the ML model.
        
        Args:
            training_data: List of log entries (dictionaries)
            labels: Optional labels (1 for attack, 0 for normal)
                    If None, uses unsupervised learning
        """
        if not training_data:
            print("No training data provided")
            return
        
        # Extract features
        feature_list = []
        for entry in training_data:
            features = self.extract_features(entry)
            feature_list.append(features)
        
        # Convert to DataFrame
        df = pd.DataFrame(feature_list)
        self.feature_names = df.columns.tolist()
        
        # Scale features
        X = self.scaler.fit_transform(df)
        
        if labels is None:
            # Unsupervised learning (Isolation Forest)
            self.model.fit(X)
        else:
            # Supervised learning (Random Forest)
            if len(set(labels)) > 1:  # Need both classes
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10
                )
                self.model.fit(X, labels)
            else:
                # Fallback to unsupervised
                self.model.fit(X)
        
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        print(f"Model trained on {len(training_data)} samples")
    
    def predict(self, log_entry):
        """Predict if log entry represents an attack.
        
        Args:
            log_entry: Dictionary containing log entry data
            
        Returns:
            Tuple of (is_attack: bool, confidence: float, details: dict)
        """
        if not self.is_trained:
            return False, 0.0, {'reason': 'Model not trained'}
        
        # Extract features
        features = self.extract_features(log_entry)
        
        # Convert to array matching training features
        feature_vector = []
        for name in self.feature_names:
            feature_vector.append(features.get(name, 0))
        
        X = np.array([feature_vector])
        X_scaled = self.scaler.transform(X)
        
        # Predict
        if hasattr(self.model, 'predict_proba'):
            # Supervised model
            prediction = self.model.predict(X_scaled)
            proba = self.model.predict_proba(X_scaled)[0]
            is_attack = prediction[0] == 1
            confidence = max(proba)
        else:
            # Unsupervised model (Isolation Forest)
            prediction = self.model.predict(X_scaled)
            score = self.model.score_samples(X_scaled)[0]
            is_attack = prediction[0] == -1  # -1 means anomaly
            # Convert score to confidence (lower score = higher anomaly)
            confidence = max(0.0, min(1.0, 1.0 - (score + 0.5)))  # Normalize score
        
        details = {
            'prediction': 'attack' if is_attack else 'normal',
            'model_type': 'supervised' if hasattr(self.model, 'predict_proba') else 'unsupervised',
            'features_used': len(self.feature_names)
        }
        
        return is_attack, confidence, details
    
    def _save_model(self):
        """Save trained model to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def get_stats(self):
        """Get detector statistics."""
        return {
            'is_trained': self.is_trained,
            'model_path': str(self.model_path),
            'feature_count': len(self.feature_names),
            'model_type': type(self.model).__name__ if self.model else 'None'
        }

