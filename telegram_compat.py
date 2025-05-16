"""
Compatibility module for python-telegram-bot to work with Python 3.13+
which no longer includes the imghdr module
"""

import sys

# Create a mock imghdr module
class MockImghdr:
    def what(self, filename, h=None):
        """Simple implementation to detect image types based on file extension"""
        if isinstance(filename, str):
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                return 'jpeg'
            elif filename.lower().endswith('.png'):
                return 'png'
            elif filename.lower().endswith('.gif'):
                return 'gif'
            elif filename.lower().endswith('.bmp'):
                return 'bmp'
            elif filename.lower().endswith('.tiff') or filename.lower().endswith('.tif'):
                return 'tiff'
        return None

# Add the mock imghdr module to sys.modules
sys.modules['imghdr'] = MockImghdr() 