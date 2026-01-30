# Quick Start Guide

Get started with the Zero-Day Attack Detection System in minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure the System

Edit `config.yaml` to set up log paths and detection thresholds:

```yaml
monitoring:
  log_paths:
    - /var/log/auth.log
    - /var/log/syslog
```

## Step 3: Generate Sample Data (Optional)

Generate sample training data to test the system:

```bash
python examples/generate_sample_logs.py --normal 1000 --suspicious 100
```

This creates:
- `training_data.jsonl` - Training data
- `labels.txt` - Labels for supervised learning

## Step 4: Train the ML Model (Optional)

Train the ML model with the generated data:

```bash
python main.py --train training_data.jsonl --labels labels.txt
```

## Step 5: Start Monitoring

Start real-time monitoring:

```bash
python main.py --monitor
```

Or analyze a specific log file:

```bash
python main.py --analyze /var/log/auth.log
```

## Step 6: Interactive Mode

Run in interactive mode for manual control:

```bash
python main.py --interactive
```

Available commands:
- `stats` - Show detection statistics
- `alerts` - View recent alerts
- `report` - Generate alert report
- `quit` - Exit

## Example Workflow

1. **Generate training data:**
   ```bash
   python examples/generate_sample_logs.py
   ```

2. **Train the model:**
   ```bash
   python main.py --train training_data.jsonl --labels labels.txt
   ```

3. **Start monitoring:**
   ```bash
   python main.py --monitor
   ```

4. **View reports:**
   Check the `./reports/` directory for generated alert reports.

## Testing with Sample Logs

Create a test log file:

```bash
echo "Jan 1 10:00:00 hostname sudo: user1 : TTY=pts/0 ; PWD=/home/user1 ; USER=root ; COMMAND=/bin/su" > test.log
```

Analyze it:

```bash
python main.py --analyze test.log
```

## Troubleshooting

### Permission Errors
If you get permission errors reading log files:
```bash
sudo python main.py --analyze /var/log/auth.log
```

### Missing Dependencies
If imports fail:
```bash
pip install --upgrade -r requirements.txt
```

### Configuration Issues
Check that `config.yaml` exists and is properly formatted:
```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## Next Steps

- Review the full [README.md](README.md) for detailed documentation
- Customize detection thresholds in `config.yaml`
- Set up email alerts for production use
- Integrate with your existing log management system

