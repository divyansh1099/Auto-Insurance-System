# Zero-Day Attack Detection System

A comprehensive system for detecting previously unknown attacks and anomalies using multiple detection methods including anomaly detection, behavioral analysis, and machine learning.

## Features

- **Multi-Layer Detection**: Combines statistical anomaly detection, behavioral pattern analysis, and ML-based detection
- **Real-Time Monitoring**: Continuously monitors log files for threats
- **Multiple Log Formats**: Supports syslog, auth logs, nginx, apache, and JSON logs
- **Alert System**: Configurable alerting via console and email
- **ML-Based Detection**: Trainable machine learning models for adaptive detection
- **Comprehensive Reporting**: Generate detailed reports of detected threats

## Architecture

The system consists of several key components:

1. **Detection Engine**: Coordinates all detection modules
2. **Anomaly Detector**: Statistical analysis using baseline comparison
3. **Behavioral Analyzer**: Pattern-based detection of suspicious behaviors
4. **ML Detector**: Machine learning-based detection using Isolation Forest or Random Forest
5. **Log Analyzer**: Parses and processes various log formats
6. **Alert System**: Generates and sends alerts for detected threats

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Zeroday
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
```bash
# Edit config.yaml with your settings
nano config.yaml
```

## Configuration

Edit `config.yaml` to configure:

- **Detection thresholds**: Adjust sensitivity for anomaly and behavioral detection
- **Log paths**: Specify which log files to monitor
- **Alert settings**: Configure email and console alerting
- **ML model settings**: Configure model training and retraining intervals

## Usage

### Real-Time Monitoring

Start the system to monitor logs in real-time:

```bash
python main.py --monitor
```

### Analyze a Log File

Analyze a specific log file:

```bash
python main.py --analyze /var/log/auth.log
```

### Train ML Model

Train the machine learning model with your data:

```bash
# Unsupervised learning (no labels)
python main.py --train training_data.jsonl

# Supervised learning (with labels)
python main.py --train training_data.jsonl --labels labels.txt
```

### Interactive Mode

Run in interactive mode for manual control:

```bash
python main.py --interactive
```

Available commands:
- `help` - Show available commands
- `stats` - Display detection statistics
- `alerts` - Show recent alerts
- `report` - Generate alert report
- `quit` - Exit the system

## Training Data Format

Training data should be in JSON Lines format (one JSON object per line):

```json
{"timestamp": 1234567890, "source_ip": "192.168.1.1", "user": "admin", "message": "sudo su", "action": "sudo"}
{"timestamp": 1234567891, "source_ip": "192.168.1.2", "user": "user1", "message": "ls -la", "action": "ls"}
```

For supervised learning, labels file should contain one label per line (0 for normal, 1 for attack).

## Detection Methods

### 1. Anomaly Detection

Uses statistical methods to detect deviations from baseline behavior:
- Z-score analysis
- Feature-based anomaly scoring
- Adaptive baseline learning

### 2. Behavioral Analysis

Detects suspicious patterns:
- Unusual request frequency
- Privilege escalation attempts
- Command pattern analysis
- Data exfiltration patterns
- Unusual access patterns

### 3. ML-Based Detection

Machine learning models for adaptive detection:
- Isolation Forest for unsupervised anomaly detection
- Random Forest for supervised classification
- Feature extraction from log entries
- Automatic model retraining

## Alert Severity Levels

- **Low**: Minor anomalies detected
- **Medium**: Suspicious behavior detected
- **High**: High-confidence threat detection
- **Critical**: Multiple detection methods flag the same threat

## Output

The system generates:

- **Console Alerts**: Real-time colored alerts in the terminal
- **Log Files**: Detailed logs in `./logs/`
- **Alert Reports**: JSON and text reports in `./reports/`
- **ML Models**: Trained models saved in `./models/`

## Project Structure

```
Zeroday/
├── src/
│   ├── core/
│   │   ├── detection_engine.py    # Main detection engine
│   │   └── alert_system.py        # Alert generation
│   ├── detectors/
│   │   ├── anomaly_detector.py    # Statistical anomaly detection
│   │   ├── behavioral_analyzer.py # Behavioral pattern analysis
│   │   └── ml_detector.py         # ML-based detection
│   ├── analyzers/
│   │   └── log_analyzer.py        # Log parsing and analysis
│   └── utils/
│       ├── config_loader.py        # Configuration management
│       └── logger.py              # Logging utilities
├── config.yaml                     # Configuration file
├── requirements.txt               # Python dependencies
├── main.py                        # Main entry point
└── README.md                      # This file
```

## Requirements

- Python 3.8+
- See `requirements.txt` for full dependency list

## Security Considerations

- This system is designed for detection, not prevention
- Ensure log files have appropriate permissions
- Store configuration files securely
- Use environment variables for sensitive credentials (email passwords, etc.)
- Regularly update and retrain ML models

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed

## License

[Specify your license here]

## Support

For issues and questions, please open an issue on the repository.

## Future Enhancements

- [ ] Web dashboard for visualization
- [ ] Database backend for alert storage
- [ ] Integration with SIEM systems
- [ ] Advanced ML models (LSTM, Transformer-based)
- [ ] Distributed monitoring capabilities
- [ ] Automated response actions

