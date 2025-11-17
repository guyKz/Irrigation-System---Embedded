"""
Smart Irrigation Bridge - Main Application
Bridges TinkerCAD simulation to ThingsBoard IoT platform
"""
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from config package
from config import settings
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Import local modules
from thingsboard_client import ThingsBoardClient
from data_processor import DataProcessor, format_telemetry
from browser_automation import TinkerCADAutomation, SerialMonitor


# ===== Logging Setup =====
def setup_logging():
    """Configure logging for the application"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce playwright logging noise
    logging.getLogger("playwright").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# ===== Rate Limiter =====
class RateLimiter:
    """Simple rate limiter for telemetry sending"""
    
    def __init__(self, max_hz: float):
        """
        Initialize rate limiter
        
        Args:
            max_hz: Maximum messages per second
        """
        self.min_interval = 1.0 / max_hz
        self.last_send_time = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        elapsed = now - self.last_send_time
        wait_time = self.min_interval - elapsed
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        self.last_send_time = time.time()


# ===== Main Application =====
def run_bridge():
    """Main bridge application logic"""
    
    # Validate configuration
    logger.info("Starting Smart Irrigation Bridge...")
    settings.print_config_summary()
    
    errors = settings.validate_config()
    if errors:
        logger.error("Configuration errors detected:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("Please check config/settings.py")
        return False
    
    # Initialize components
    logger.info("Initializing components...")
    
    tb_client = ThingsBoardClient(
        host=settings.TB_HOST,
        token=settings.TB_TOKEN,
        use_https=settings.USE_HTTPS
    )
    
    data_processor = DataProcessor()
    rate_limiter = RateLimiter(settings.MAX_SEND_HZ)
    
    # Test ThingsBoard connection
    if not tb_client.test_connection():
        logger.error("Failed to connect to ThingsBoard. Check your configuration.")
        return False
    
    # Start browser automation
    logger.info("Starting browser automation...")
    
    with sync_playwright() as playwright:
        # Launch browser
        browser = playwright.chromium.launch(headless=settings.HEADLESS)
        context = browser.new_context(**playwright.devices[settings.BROWSER_DEVICE])
        page = context.new_page()
        
        # Initialize automation
        automation = TinkerCADAutomation(page)
        
        # Login to TinkerCAD
        success = automation.navigate_and_login(
            circuit_url=settings.TINKERCAD_CIRCUIT_URL,
            class_code=settings.TINKERCAD_CLASS_CODE,
            login_code=settings.TINKERCAD_LOGIN_CODE
        )
        
        if not success:
            logger.error("Failed to login to TinkerCAD")
            browser.close()
            return False
        
        # Setup simulation
        success = automation.setup_simulation()
        if not success:
            logger.error("Failed to setup simulation")
            browser.close()
            return False
        
        # Open ThingsBoard dashboard in new tab
        logger.info("Opening ThingsBoard dashboard...")
        dashboard_page = context.new_page()
        dashboard_page.goto(settings.TB_DASHBOARD_URL)
        logger.info(f"✓ Dashboard opened: {settings.TB_DASHBOARD_URL}")
        
        # Initialize serial monitor
        serial_monitor = SerialMonitor(automation)
        
        # Main monitoring loop
        logger.info("=" * 60)
        logger.info("BRIDGE ACTIVE - Monitoring serial output...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        message_count = 0
        start_time = time.time()
        
        try:
            while True:
                # Read new serial content
                new_content = serial_monitor.get_new_content()
                
                if new_content:
                    # Process and extract JSON objects
                    json_objects = data_processor.add_chunk(new_content)
                    
                    for data in json_objects:
                        # Wait for rate limit
                        rate_limiter.wait_if_needed()
                        
                        # Preview data if enabled
                        if settings.PRINT_PREVIEW:
                            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sending: {format_telemetry(data)}")
                        
                        # Send to ThingsBoard
                        success = tb_client.send_telemetry(data)
                        
                        if success:
                            message_count += 1
                            print(f"✓ Message #{message_count} sent successfully")
                        else:
                            print(f"✗ Failed to send message")
                
                # Poll interval
                time.sleep(settings.POLL_SEC)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("Stopping bridge (Ctrl+C detected)")
            logger.info("=" * 60)
            
            # Print statistics
            runtime = time.time() - start_time
            logger.info(f"\nRuntime: {runtime:.1f} seconds")
            logger.info(f"Messages sent: {message_count}")
            if runtime > 0:
                logger.info(f"Average rate: {message_count / runtime:.2f} msg/s")
            
            data_processor.print_stats()
            tb_client.print_stats()
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            
        finally:
            # Cleanup
            logger.info("Cleaning up...")
            automation.stop_simulation()
            context.close()
            browser.close()
            logger.info("✓ Browser closed")
    
    logger.info("Bridge stopped successfully")
    return True


# ===== Entry Point =====
def main():
    """Application entry point"""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("SMART IRRIGATION SYSTEM - TINKERCAD TO THINGSBOARD BRIDGE")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {settings.LOG_FILE}")
    logger.info("=" * 60)
    
    try:
        success = run_bridge()
        exit_code = 0 if success else 1
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        exit_code = 1
    
    logger.info("=" * 60)
    logger.info("Application terminated")
    logger.info("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
