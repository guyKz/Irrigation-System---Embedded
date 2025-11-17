"""
Data Processor
Parses and validates serial monitor output from TinkerCAD
"""
import re
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Regex to extract complete JSON objects from text
JSON_PATTERN = re.compile(r"\{.*?\}", flags=re.DOTALL)


class DataProcessor:
    """Processes serial data from TinkerCAD simulation"""
    
    def __init__(self):
        """Initialize data processor"""
        self.buffer = ""
        self.total_received = 0
        self.total_parsed = 0
        self.total_invalid = 0
        
        logger.info("Data processor initialized")
    
    def add_chunk(self, text: str) -> List[Dict]:
        """
        Add text chunk and extract valid JSON objects
        
        Args:
            text: New text from serial monitor
            
        Returns:
            List of valid JSON dictionaries
        """
        self.buffer += text
        valid_objects = []
        
        # Find all JSON-like patterns
        matches = list(JSON_PATTERN.finditer(self.buffer))
        
        if matches:
            # Keep trailing partial text for next iteration
            end_of_last = matches[-1].end()
            remaining_buffer = self.buffer[end_of_last:]
            
            # Process each potential JSON object
            for match in matches:
                candidate = match.group()
                self.total_received += 1
                
                parsed = self._parse_json(candidate)
                if parsed is not None:
                    valid_objects.append(parsed)
                    self.total_parsed += 1
                else:
                    self.total_invalid += 1
            
            # Update buffer with remaining text
            self.buffer = remaining_buffer
            
            logger.debug(f"Extracted {len(valid_objects)} valid JSON objects")
        
        return valid_objects
    
    def _parse_json(self, text: str) -> Optional[Dict]:
        """
        Parse JSON text safely
        
        Args:
            text: JSON string to parse
            
        Returns:
            Dictionary if valid JSON object, None otherwise
        """
        try:
            data = json.loads(text)
            
            # Only accept dictionaries (objects)
            if not isinstance(data, dict):
                logger.debug(f"Skipped non-dict JSON: {type(data)}")
                return None
            
            # Validate it has at least one key
            if not data:
                logger.debug("Skipped empty JSON object")
                return None
            
            return data
            
        except json.JSONDecodeError as e:
            logger.debug(f"Invalid JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error parsing JSON: {e}")
            return None
    
    def clear_buffer(self):
        """Clear internal buffer (useful on simulation reset)"""
        logger.debug(f"Clearing buffer ({len(self.buffer)} chars)")
        self.buffer = ""
    
    def get_stats(self) -> Dict:
        """
        Get processor statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_received": self.total_received,
            "total_parsed": self.total_parsed,
            "total_invalid": self.total_invalid,
            "parse_rate": (
                self.total_parsed / self.total_received * 100
                if self.total_received > 0
                else 0
            ),
            "buffer_size": len(self.buffer)
        }
    
    def print_stats(self):
        """Print statistics to console"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("DATA PROCESSOR STATISTICS")
        print("=" * 60)
        print(f"Total Received:  {stats['total_received']}")
        print(f"Successfully Parsed: {stats['total_parsed']}")
        print(f"Invalid/Skipped: {stats['total_invalid']}")
        print(f"Parse Success Rate: {stats['parse_rate']:.1f}%")
        print(f"Buffer Size:     {stats['buffer_size']} chars")
        print("=" * 60 + "\n")


def format_telemetry(data: Dict) -> str:
    """
    Format telemetry data for display
    
    Args:
        data: Telemetry dictionary
        
    Returns:
        Formatted string
    """
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def validate_telemetry(data: Dict) -> bool:
    """
    Validate telemetry data has expected fields
    
    Args:
        data: Telemetry dictionary
        
    Returns:
        True if valid
    """
    # Expected fields from your Arduino code
    expected_fields = {
        "moisture", "temp", "humidity", "pump", "zone1", 
        "zone2", "light", "water", "mode", "cycles", "uptime"
    }
    
    # Check if at least some expected fields are present
    present_fields = set(data.keys())
    common_fields = expected_fields & present_fields
    
    # Valid if at least 3 expected fields present
    return len(common_fields) >= 3