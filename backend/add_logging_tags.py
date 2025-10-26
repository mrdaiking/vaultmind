#!/usr/bin/env python3
"""
Script to add structured logging tags to Python files
"""
import re
import sys

def add_logging_tags(filename, tag):
    """Add logging tags to a file"""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Replace logger.info/error/warning/debug statements
    replacements = [
        # Info statements
        (r'logger\.info\("', f'logger.info("[{tag}] '),
        (r'logger\.info\(f"', f'logger.info(f"[{tag}] '),
        (r"logger\.info\('", f"logger.info('[{tag}] '),
        (r"logger\.info\(f'", f"logger.info(f'[{tag}] '),
        
        # Error statements  
        (r'logger\.error\("', f'logger.error("[{tag}][ERROR] '),
        (r'logger\.error\(f"', f'logger.error(f"[{tag}][ERROR] '),
        (r"logger\.error\('", f"logger.error('[{tag}][ERROR] '),
        (r"logger\.error\(f'", f"logger.error(f'[{tag}][ERROR] '),
        
        # Warning statements
        (r'logger\.warning\("', f'logger.warning("[{tag}] '),
        (r'logger\.warning\(f"', f'logger.warning(f"[{tag}] '),
        (r"logger\.warning\('", f"logger.warning('[{tag}] '),
        (r"logger\.warning\(f'", f"logger.warning(f'[{tag}] '),
        
        # Debug statements
        (r'logger\.debug\("', f'logger.debug("[{tag}] '),
        (r'logger\.debug\(f"', f'logger.debug(f"[{tag}] '),
        (r"logger\.debug\('", f"logger.debug('[{tag}] '),
        (r"logger\.debug\(f'", f"logger.debug(f'[{tag}] '),
    ]
    
    for pattern, replacement in replacements:
        # Only replace if tag not already present
        content = re.sub(pattern, replacement, content)
    
    # Remove duplicate tags (in case already tagged)
    content = re.sub(r'\[' + tag + r'\]\s*\[' + tag + r'\]', f'[{tag}]', content)
    content = re.sub(r'\[' + tag + r'\]\[ERROR\]\s*\[' + tag + r'\]\[ERROR\]', f'[{tag}][ERROR]', content)
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Added [{tag}] tags to {filename}")

# Add tags to google_calendar.py
add_logging_tags('google_calendar.py', 'CALENDAR')

# Fix AUTH tags for token retrieval function
with open('google_calendar.py', 'r') as f:
    content = f.read()

# Replace CALENDAR with AUTH in the get_google_access_token_from_auth0 function
auth_function_start = content.find('async def get_google_access_token_from_auth0')
if auth_function_start != -1:
    # Find the end of this function (next async def or end of file)
    next_function = content.find('async def', auth_function_start + 10)
    if next_function == -1:
        next_function = len(content)
    
    # Replace CALENDAR with AUTH in this section
    before = content[:auth_function_start]
    function_section = content[auth_function_start:next_function]
    after = content[next_function:]
    
    function_section = function_section.replace('[CALENDAR]', '[AUTH]')
    
    content = before + function_section + after
    
    with open('google_calendar.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed AUTH tags in google_calendar.py")

print("\n📊 Summary:")
print("- [MGMT] tags already in auth0_management.py")
print("- [CALENDAR] tags added to google_calendar.py")
print("- [AUTH] tags added to google_calendar.py (token retrieval)")
print("\nNext: Run this script, then add tags to main.py manually for AI and API sections")