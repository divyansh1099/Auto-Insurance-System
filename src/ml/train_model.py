"""
Risk Scoring Model Training

Trains an XGBoost model for driver risk assessment.
"""

import os
import json
import argparse
import pickle
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV, cross_val_score
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    explained_variance_score
)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
import seaborn as sns

from feature_engineering import FeatureEngineer


class RiskScoringModel:
    """XGBoost-based risk scoring model."""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "v1.0"

    def prepare_training_data(
        self,
        features_df: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare data for training.

        Args:
            features_df: DataFrame with features and target
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        # Separate features and target
        if 'risk_score' not in features_df.columns:
            raise ValueError("'risk_score' column not found in features DataFrame")

        X = features_df.drop('risk_score', axis=1)
        y = features_df['risk_score']

        # Store feature names
        self.feature_names = list(X.columns)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state
        )

        return X_train, X_test, y_train, y_test

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None,
        tune_hyperparameters: bool = False
    ) -> xgb.XGBRegressor:
        """
        Train the XGBoost model.

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            tune_hyperparameters: Whether to perform hyperparameter tuning

        Returns:
            Trained XGBoost model
        """
        if tune_hyperparameters:
            print("Performing hyperparameter tuning...")
            param_distributions = {
                'max_depth': [3, 4, 5, 6, 7],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'n_estimators': [100, 200, 300],
                'subsample': [0.6, 0.7, 0.8, 0.9],
                'colsample_bytree': [0.6, 0.7, 0.8, 0.9],
                'min_child_weight': [1, 3, 5],
                'gamma': [0, 0.1, 0.2]
            }

            xgb_model = xgb.XGBRegressor(
                objective='reg:squarederror',
                random_state=42
            )

            random_search = RandomizedSearchCV(
                xgb_model,
                param_distributions,
                n_iter=20,
                cv=5,
                scoring='neg_mean_squared_error',
                n_jobs=-1,
                random_state=42,
                verbose=1
            )

            random_search.fit(X_train, y_train)
            self.model = random_search.best_estimator_

            print(f"Best parameters: {random_search.best_params_}")
            print(f"Best CV score: {-random_search.best_score_:.4f}")

        else:
            print("Training with default hyperparameters...")
            # Create validation set for early stopping
            from sklearn.model_selection import train_test_split
            X_train_fit, X_val_fit, y_train_fit, y_val_fit = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42
            )
            
            # Optimized XGBoost parameters for risk scoring
            self.model = xgb.XGBRegressor(
                max_depth=6,  # Increased depth for better feature interactions
                learning_rate=0.05,  # Lower learning rate for better generalization
                n_estimators=300,  # More trees for better accuracy
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                gamma=0.1,
                reg_alpha=0.1,  # L1 regularization
                reg_lambda=1.0,  # L2 regularization
                objective='reg:squarederror',
                random_state=42,
                n_jobs=-1  # Use all CPU cores
            )

            self.model.fit(
                X_train_fit,
                y_train_fit,
                eval_set=[(X_val_fit, y_val_fit)],
                early_stopping_rounds=20,  # Stop early if no improvement
                verbose=False
            )

        return self.model

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate the model.

        Args:
            X_test: Test features
            y_test: Test target

        Returns:
            Dictionary of evaluation metrics
        """
        predictions = self.model.predict(X_test)

        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
            'mae': mean_absolute_error(y_test, predictions),
            'r2': r2_score(y_test, predictions),
            'explained_variance': explained_variance_score(y_test, predictions)
        }

        print("\nModel Performance:")
        print(f"  RMSE: {metrics['rmse']:.4f}")
        print(f"  MAE: {metrics['mae']:.4f}")
        print(f"  R²: {metrics['r2']:.4f}")
        print(f"  Explained Variance: {metrics['explained_variance']:.4f}")

        # Evaluate by risk bucket
        y_test_buckets = pd.cut(
            y_test,
            bins=[0, 20, 40, 60, 80, 100],
            labels=['Excellent', 'Good', 'Average', 'Below Average', 'High Risk']
        )
        pred_buckets = pd.cut(
            predictions,
            bins=[0, 20, 40, 60, 80, 100],
            labels=['Excellent', 'Good', 'Average', 'Below Average', 'High Risk']
        )

        bucket_accuracy = (y_test_buckets == pred_buckets).mean()
        print(f"  Bucket Classification Accuracy: {bucket_accuracy:.4f}")

        return metrics

    def explain_predictions(self, X_sample: pd.DataFrame, n_samples: int = 100):
        """
        Generate SHAP explanations.

        Args:
            X_sample: Sample data for SHAP analysis
            n_samples: Number of samples to use

        Returns:
            SHAP explainer and values
        """
        print("\nGenerating SHAP explanations...")

        # Use a subset of data for SHAP
        X_subset = X_sample.sample(min(n_samples, len(X_sample)), random_state=42)

        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X_subset)

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('importance', ascending=False)

        print("\nTop 10 Most Important Features:")
        print(feature_importance.head(10).to_string(index=False))

        return explainer, shap_values, feature_importance

    def save_model(self, output_dir: str = "./models"):
        """Save the trained model."""
        os.makedirs(output_dir, exist_ok=True)

        model_path = os.path.join(output_dir, f"risk_model_{self.model_version}.pkl")

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'version': self.model_version,
            'trained_at': datetime.now().isoformat()
        }

        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"\nModel saved to: {model_path}")

    def load_model(self, model_path: str):
        """Load a trained model."""
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.model_version = model_data['version']

        print(f"Model loaded from: {model_path}")


def create_synthetic_training_data(n_drivers: int = 500) -> pd.DataFrame:
    """
    Create synthetic training data for demonstration.

    In production, this would come from the database.
    """
    print(f"Creating synthetic training data for {n_drivers} drivers...")

    feature_engineer = FeatureEngineer()
    all_features = []

    for i in range(n_drivers):
        # Random driver profile
        profile = np.random.choice(['safe', 'average', 'risky'], p=[0.4, 0.45, 0.15])

        # Generate features based on profile
        if profile == 'safe':
            harsh_braking = np.random.uniform(0, 3)
            rapid_accel = np.random.uniform(0, 2)
            speeding = np.random.uniform(0, 5)
            max_speed = np.random.uniform(50, 70)
            night_driving = np.random.uniform(0, 15)
        elif profile == 'average':
            harsh_braking = np.random.uniform(2, 6)
            rapid_accel = np.random.uniform(2, 5)
            speeding = np.random.uniform(3, 10)
            max_speed = np.random.uniform(60, 85)
            night_driving = np.random.uniform(10, 25)
        else:  # risky
            harsh_braking = np.random.uniform(5, 12)
            rapid_accel = np.random.uniform(5, 10)
            speeding = np.random.uniform(8, 20)
            max_speed = np.random.uniform(75, 105)
            night_driving = np.random.uniform(20, 40)

        features = {
            'avg_speed_overall': np.random.uniform(30, 50),
            'max_speed_recorded': max_speed,
            'speed_variance': np.random.uniform(5, 15),
            'speeding_incidents_per_100mi': speeding,
            'harsh_braking_per_100mi': harsh_braking,
            'rapid_accel_per_100mi': rapid_accel,
            'smooth_driving_score': 100 - (harsh_braking + rapid_accel) * 3,
            'night_driving_pct': night_driving,
            'rush_hour_pct': np.random.uniform(20, 60),
            'weekend_driving_pct': np.random.uniform(10, 40),
            'late_night_driving_pct': np.random.uniform(0, 15),
            'avg_trip_duration_min': np.random.uniform(15, 45),
            'avg_trip_distance_miles': np.random.uniform(10, 30),
            'total_trips': np.random.randint(50, 200),
            'trip_consistency_score': np.random.uniform(50, 95),
            'total_miles': np.random.uniform(500, 2000),
            'phone_usage_trip_pct': np.random.uniform(0, 20),
            'harsh_corner_per_100mi': np.random.uniform(0, 5),
            'age': np.random.randint(18, 70),
            'years_licensed': np.random.randint(1, 50),
            'vehicle_age': np.random.randint(0, 15),
            'vehicle_safety_rating': np.random.randint(1, 6)
        }

        # Calculate interaction features for synthetic data
        interactions = feature_engineer.calculate_interaction_features(features)
        features.update(interactions)

        # Calculate risk score target with some noise
        base_risk_score = feature_engineer.create_risk_score_target(features)
        
        # Add random noise to make it realistic (target isn't perfectly linear)
        noise = np.random.normal(0, 5) # Standard deviation of 5 points
        risk_score = min(max(base_risk_score + noise, 0), 100)
        
        features['risk_score'] = risk_score

        all_features.append(features)

    return pd.DataFrame(all_features)


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description='Train risk scoring model')
    parser.add_argument('--n-drivers', type=int, default=500, help='Number of drivers for synthetic data')
    parser.add_argument('--output-dir', type=str, default='./models', help='Output directory for model')
    parser.add_argument('--tune', action='store_true', help='Perform hyperparameter tuning')
    args = parser.parse_args()

    print("=== Risk Scoring Model Training ===\n")

    # Create synthetic data (in production, load from database)
    features_df = create_synthetic_training_data(n_drivers=args.n_drivers)
    print(f"Training data shape: {features_df.shape}")

    # Initialize model
    model = RiskScoringModel()

    # Prepare data
    X_train, X_test, y_train, y_test = model.prepare_training_data(features_df)
    print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

    # Train model
    model.train(X_train, y_train, tune_hyperparameters=args.tune)

    # Evaluate model
    metrics = model.evaluate(X_test, y_test)

    # SHAP explanations
    explainer, shap_values, feature_importance = model.explain_predictions(X_test)

    # Save model
    model.save_model(output_dir=args.output_dir)

    # Save feature importance
    feature_importance_path = os.path.join(args.output_dir, 'feature_importance.csv')
    feature_importance.to_csv(feature_importance_path, index=False)
    print(f"Feature importance saved to: {feature_importance_path}")

    print("\n=== Training Complete ===")


if __name__ == "__main__":
    main()
