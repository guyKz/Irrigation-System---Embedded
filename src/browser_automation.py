"""
Browser Automation Module
Controls TinkerCAD circuit using Playwright
"""
import logging
import time
from playwright.sync_api import Page, TimeoutError as PWTimeout
from typing import Optional

logger = logging.getLogger(__name__)


class TinkerCADAutomation:
    """Automates TinkerCAD circuit simulation using Playwright"""
    
    def __init__(self, page: Page):
        """
        Initialize automation with Playwright page
        
        Args:
            page: Playwright Page object
        """
        self.page = page
        self.serial_locator = None
        self.is_simulation_running = False
        
        logger.info("TinkerCAD automation initialized")
    
    def navigate_and_login(
        self,
        circuit_url: str,
        class_code: str,
        login_code: str
    ) -> bool:
        """
        Navigate to TinkerCAD and login
        
        Args:
            circuit_url: Full URL to the circuit
            class_code: TinkerCAD class code
            login_code: TinkerCAD login code
            
        Returns:
            True if successful
        """
        try:
            logger.info("Navigating to TinkerCAD...")
            logger.info(f"Circuit URL: {circuit_url}")
            
            # Navigate to circuit URL (this will redirect to login)
            self.page.goto(circuit_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            
            logger.info("Attempting login...")
            
            # Click "Students with Class Code"
            logger.debug("Looking for 'Students with Class Code' button...")
            try:
                self.page.get_by_role("link", name="Students with Class Code").click(timeout=5000)
                time.sleep(1)
            except:
                logger.warning("Could not find 'Students with Class Code' button, may already be on login page")
            
            # Enter class code
            logger.debug(f"Entering class code: {class_code}")
            try:
                self.page.get_by_placeholder("Like: 123 456").fill(class_code)
                time.sleep(0.5)
            except:
                logger.warning("Class code field not found, trying alternative...")
                self.page.locator("input[placeholder*='123']").fill(class_code)
                time.sleep(0.5)
            
            # Click "Go to my class"
            logger.debug("Clicking 'Go to my class'...")
            try:
                self.page.locator("button").filter(has_text="Go to my class").click()
                time.sleep(2)
            except:
                logger.warning("'Go to my class' button not found, trying alternative...")
                self.page.locator("button:has-text('Go to my class')").click()
                time.sleep(2)
            
            # Click "Join with Login code"
            logger.debug("Clicking 'Join with Login code'...")
            try:
                self.page.get_by_text("Join with Login code").click()
                time.sleep(1)
            except:
                logger.warning("'Join with Login code' not found, trying alternative...")
                self.page.locator("text=Join with Login code").click()
                time.sleep(1)
            
            # Enter login code
            logger.debug(f"Entering login code: {login_code}")
            try:
                self.page.get_by_placeholder("Type your login code").fill(login_code)
                time.sleep(0.5)
            except:
                logger.warning("Login code field not found, trying alternative...")
                self.page.locator("input[placeholder*='login code']").fill(login_code)
                time.sleep(0.5)
            
            # Final "Go to my class"
            logger.debug("Final 'Go to my class' click...")
            try:
                self.page.get_by_text("Go to my class").click()
            except:
                self.page.locator("button:has-text('Go to my class')").click()
            
            # Wait for navigation after login
            logger.info("Waiting for login to complete...")
            time.sleep(5)
            
            # NOW navigate to the actual circuit URL
            logger.info("Navigating to circuit after login...")
            self.page.goto(circuit_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            logger.info("✓ Login successful and navigated to circuit")
            return True
            
        except PWTimeout as e:
            logger.error(f"Timeout during login: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def setup_simulation(self) -> bool:
        """
        Open code editor, serial monitor, and start simulation
        
        Returns:
            True if successful
        """
        try:
            logger.info("Setting up simulation environment...")
            
            # Wait a bit for the page to fully load
            time.sleep(2)
            
            # Open Code Editor
            logger.debug("Opening Code Editor...")
            try:
                self.page.locator("#CODE_EDITOR_ID").click(timeout=10000)
            except:
                logger.warning("CODE_EDITOR_ID not found, trying alternative...")
                self.page.locator("[id*='CODE'], [class*='code-editor']").first.click()
            time.sleep(1)
            
            # Open Serial Monitor
            logger.debug("Opening Serial Monitor...")
            try:
                self.page.locator("#SERIAL_MONITOR_ID").click(timeout=10000)
            except:
                logger.warning("SERIAL_MONITOR_ID not found, trying alternative...")
                self.page.locator("[id*='SERIAL'], [class*='serial']").first.click()
            time.sleep(1)
            
            # Start Simulation
            logger.debug("Starting simulation...")
            try:
                self.page.locator("#SIMULATION_ID").click(timeout=10000)
            except:
                logger.warning("SIMULATION_ID not found, trying alternative...")
                # Try to find Start Simulation button by text
                self.page.locator("button:has-text('Start Simulation')").click()
            time.sleep(2)
            
            # Wait for serial monitor to be visible
            logger.debug("Waiting for serial monitor output...")
            serial_selector = ".code_panel__serial__content__text"
            self.serial_locator = self.page.locator(serial_selector)
            
            try:
                self.serial_locator.wait_for(state="visible", timeout=15000)
            except:
                logger.warning("Standard serial selector not found, trying alternatives...")
                # Try alternative selectors
                alternative_selectors = [
                    ".serial-monitor-content",
                    "[class*='serial']",
                    ".code-panel-serial",
                    "div.serial"
                ]
                for selector in alternative_selectors:
                    try:
                        self.serial_locator = self.page.locator(selector)
                        self.serial_locator.wait_for(state="visible", timeout=5000)
                        logger.info(f"Found serial monitor with selector: {selector}")
                        break
                    except:
                        continue
            
            self.is_simulation_running = True
            logger.info("✓ Simulation setup complete")
            return True
            
        except PWTimeout as e:
            logger.error(f"Timeout setting up simulation: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting up simulation: {e}")
            return False
    
    def read_serial_output(self) -> Optional[str]:
        """
        Read current serial monitor output
        
        Returns:
            Serial text or None if error
        """
        if not self.serial_locator:
            logger.error("Serial locator not initialized")
            return None
        
        try:
            text = self.serial_locator.inner_text() or ""
            # Normalize line endings
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            return text
            
        except PWTimeout:
            logger.debug("Timeout reading serial output")
            return None
        except Exception as e:
            logger.warning(f"Error reading serial output: {e}")
            return None
    
    def is_running(self) -> bool:
        """Check if simulation is running"""
        return self.is_simulation_running
    
    def stop_simulation(self):
        """Stop the simulation"""
        try:
            logger.info("Stopping simulation...")
            # Click simulation button again to stop
            self.page.locator("#SIMULATION_ID").click()
            self.is_simulation_running = False
            logger.info("✓ Simulation stopped")
        except Exception as e:
            logger.warning(f"Error stopping simulation: {e}")


class SerialMonitor:
    """Monitors serial output and tracks changes"""
    
    def __init__(self, automation: TinkerCADAutomation):
        """
        Initialize serial monitor
        
        Args:
            automation: TinkerCADAutomation instance
        """
        self.automation = automation
        self.last_text_length = 0
        self.total_reads = 0
        
        logger.info("Serial monitor initialized")
    
    def get_new_content(self) -> str:
        """
        Get only new content since last read
        
        Returns:
            New text content
        """
        full_text = self.automation.read_serial_output()
        
        if full_text is None:
            return ""
        
        self.total_reads += 1
        current_length = len(full_text)
        
        # Detect simulation reset (content cleared)
        if current_length < self.last_text_length:
            logger.info("Simulation reset detected")
            self.last_text_length = 0
        
        # Extract only new content
        new_content = full_text[self.last_text_length:]
        self.last_text_length = current_length
        
        if new_content:
            logger.debug(f"New content: {len(new_content)} chars")
        
        return new_content
    
    def reset(self):
        """Reset tracking (useful after simulation restart)"""
        logger.debug("Resetting serial monitor tracking")
        self.last_text_length = 0