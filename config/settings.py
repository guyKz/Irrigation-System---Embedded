"""
Configuration settings for TinkerCAD-ThingsBoard Bridge
"""
import os
from pathlib import Path

# ===== Project Paths =====
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)

# ===== TinkerCAD Configuration =====
TINKERCAD_CIRCUIT_URL = "https://www.tinkercad.com/things/hTrSolRa4D1-smooth-jaiks-borwo/editel?returnTo=https%3A%2F%2Fwww.tinkercad.com%2Fdashboard%2Fdesigns%2Fcircuits&sharecode=WyCaIdMpHj_ctZyKmGF_-gRhH7uQz4xmHD_nGaFIFyM"
TINKERCAD_CLASS_CODE = os.getenv("TINKERCAD_CLASS_CODE", "6YWGRSYQF")
TINKERCAD_LOGIN_CODE = os.getenv("TINKERCAD_LOGIN_CODE", "vladi")

# ===== ThingsBoard Configuration =====
TB_HOST = os.getenv("TB_HOST", "eu.thingsboard.cloud")
TB_TOKEN = os.getenv("TB_TOKEN", "CY1zWMnlhydkKr0Hx9rG").strip()
TB_DASHBOARD_URL = "https://eu.thingsboard.cloud/dashboards/all/6e1fdde0-a387-11f0-89a6-d5955492b887"
USE_HTTPS = os.getenv("USE_HTTPS", "true").lower() == "true"

# ===== Bridge Behavior Settings =====
MAX_SEND_HZ = float(os.getenv("MAX_SEND_HZ", "5.0"))  # Maximum telemetry rate (messages per second)
POLL_SEC = float(os.getenv("POLL_SEC", "0.3"))  # How often to check serial monitor
PRINT_PREVIEW = os.getenv("PRINT_PREVIEW", "true").lower() == "true"  # Print data before sending
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"  # Run browser in headless mode

# ===== Serial Monitor Configuration =====
SERIAL_WAIT_TIMEOUT = 10000  # Milliseconds to wait for serial monitor
SERIAL_SELECTOR = ".code_panel__serial__content__text"  # CSS selector for serial output

# ===== Logging Configuration =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = LOGS_DIR / f"bridge_{os.getpid()}.log"

# ===== Browser Configuration =====
BROWSER_TIMEOUT = 30000  # Page load timeout in milliseconds
BROWSER_DEVICE = "Desktop Chrome HiDPI"

# ===== Validation =====
def validate_config():
    """Validate critical configuration values"""
    errors = []
    
    if not TB_TOKEN or TB_TOKEN == "YOUR_TOKEN_HERE":
        errors.append("ThingsBoard token not configured")
    
    if not TINKERCAD_CLASS_CODE or TINKERCAD_CLASS_CODE == "YOUR_CLASS_CODE":
        errors.append("TinkerCAD class code not configured")
    
    if not TINKERCAD_LOGIN_CODE or TINKERCAD_LOGIN_CODE == "YOUR_LOGIN_CODE":
        errors.append("TinkerCAD login code not configured")
    
    if MAX_SEND_HZ <= 0:
        errors.append("MAX_SEND_HZ must be positive")
    
    if POLL_SEC <= 0:
        errors.append("POLL_SEC must be positive")
    
    return errors

# ===== Display Configuration Summary =====
def print_config_summary():
    """Print configuration summary"""
    print("=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"ThingsBoard Host:      {TB_HOST}")
    print(f"ThingsBoard Token:     {TB_TOKEN[:10]}..." if len(TB_TOKEN) > 10 else TB_TOKEN)
    print(f"Use HTTPS:             {USE_HTTPS}")
    print(f"Max Send Rate:         {MAX_SEND_HZ} Hz")
    print(f"Poll Interval:         {POLL_SEC}s")
    print(f"Print Preview:         {PRINT_PREVIEW}")
    print(f"Headless Mode:         {HEADLESS}")
    print(f"Log Level:             {LOG_LEVEL}")
    print(f"Log File:              {LOG_FILE}")
    print("=" * 60)