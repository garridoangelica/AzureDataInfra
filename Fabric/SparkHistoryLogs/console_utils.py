#!/usr/bin/env python3
"""
Console Output Utilities - Cross-platform colors and emojis for PowerShell and Bash

Provides consistent, colorful output with PowerShell/Bash compatible emojis.
"""

import sys
import os

class Colors:
    """ANSI color codes for cross-platform terminal coloring"""
    
    # Reset
    RESET = '\033[0m'
    
    # Regular Colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright Colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background Colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    @classmethod
    def disable(cls):
        """Disable colors for terminals that don't support them"""
        for attr in dir(cls):
            if not attr.startswith('_') and attr != 'disable':
                setattr(cls, attr, '')

# Disable colors if not in a supported terminal
if os.getenv('NO_COLOR') or (sys.platform == 'win32' and os.getenv('TERM') != 'xterm'):
    # Check if we're in Windows Terminal or VS Code which support ANSI
    if not (os.getenv('WT_SESSION') or os.getenv('VSCODE_PID')):
        # Only disable if we're in old Command Prompt
        pass  # Keep colors enabled by default

# Detect if we're in Windows Command Prompt (which doesn't support Unicode well)
def _is_cmd_prompt():
    """Detect if running in Windows Command Prompt vs PowerShell/Terminal"""
    if sys.platform != 'win32':
        return False
    # Check environment variables that indicate modern terminals
    return not (os.getenv('WT_SESSION') or os.getenv('VSCODE_PID') or 
                os.getenv('TERM') or os.getenv('ConEmuANSI'))

# Create a singleton emoji instance that adapts to the terminal
class _EmojiSingleton:
    """Cross-platform compatible emojis for PowerShell and Bash"""
    
    def __init__(self):
        self._use_ascii = _is_cmd_prompt()
    
    @property
    def SUCCESS(self):
        return "[+]" if self._use_ascii else "✓"
    
    @property
    def ERROR(self):
        return "[!]" if self._use_ascii else "✗"
    
    @property
    def WARNING(self):
        return "[*]" if self._use_ascii else "⚠"
    
    @property
    def INFO(self):
        return "[i]" if self._use_ascii else "ℹ"
    
    @property
    def PROCESS(self):
        return ">>>" if self._use_ascii else "▶"
    
    @property
    def ROCKET(self):
        return "=>" if self._use_ascii else "→"
    
    @property
    def GEAR(self):
        return "[*]" if self._use_ascii else "⚙"
    
    @property
    def CLOCK(self):
        return "[T]" if self._use_ascii else "⏱"
    
    @property
    def TARGET(self):
        return "(o)" if self._use_ascii else "◉"
    
    @property
    def FOLDER(self):
        return "[DIR]" if self._use_ascii else "📁"
    
    @property
    def FILE(self):
        return "[FILE]" if self._use_ascii else "📄"
    
    @property
    def PACKAGE(self):
        return "[PKG]" if self._use_ascii else "📦"
    
    @property
    def MAGNIFY(self):
        return "[SCAN]" if self._use_ascii else "🔍"
    
    @property
    def CHART(self):
        return "[STATS]" if self._use_ascii else "📊"
    
    @property
    def SHIELD(self):
        return "[SEC]" if self._use_ascii else "🛡"
    
    @property
    def KEY(self):
        return "[KEY]" if self._use_ascii else "🔑"
    
    @property
    def LOCK(self):
        return "[LOCK]" if self._use_ascii else "🔒"
    
    @property
    def UNLOCK(self):
        return "[OPEN]" if self._use_ascii else "🔓"
    
    @property
    def GLOBE(self):
        return "[NET]" if self._use_ascii else "🌐"
    
    @property
    def LINK(self):
        return "[LINK]" if self._use_ascii else "🔗"
    
    @property
    def WIFI(self):
        return "[WIFI]" if self._use_ascii else "📡"
    
    @property  
    def warning(self):
        return "[!]" if self._use_ascii else "🚨"
    
    @property
    def check_mark(self):
        return "[OK]" if self._use_ascii else "✅"
    
    @property
    def globe(self):
        return "[NET]" if self._use_ascii else "🌐"

# Create the singleton instance
Emoji = _EmojiSingleton()

def print_success(message: str, use_alt: bool = False):
    """Print success message in green with checkmark"""
    emoji = Emoji.ALT_SUCCESS if use_alt else Emoji.SUCCESS
    print(f"{Colors.BRIGHT_GREEN}{emoji} {message}{Colors.RESET}")

def print_error(message: str, use_alt: bool = False):
    """Print error message in red with X mark"""
    emoji = Emoji.ALT_ERROR if use_alt else Emoji.ERROR
    print(f"{Colors.BRIGHT_RED}{emoji} {message}{Colors.RESET}")

def print_warning(message: str, use_alt: bool = False):
    """Print warning message in yellow with warning sign"""
    emoji = Emoji.ALT_WARNING if use_alt else Emoji.WARNING
    print(f"{Colors.BRIGHT_YELLOW}{emoji} {message}{Colors.RESET}")

def print_info(message: str, use_alt: bool = False):
    """Print info message in cyan with info sign"""
    emoji = Emoji.ALT_INFO if use_alt else Emoji.INFO
    print(f"{Colors.BRIGHT_CYAN}{emoji} {message}{Colors.RESET}")

def print_process(message: str, use_alt: bool = False):
    """Print process message in blue with arrow"""
    emoji = Emoji.ALT_PROCESS if use_alt else Emoji.PROCESS
    print(f"{Colors.BRIGHT_BLUE}{emoji} {message}{Colors.RESET}")

def print_header(title: str, width: int = 70):
    """Print colored header with separators"""
    print(f"\n{Colors.BRIGHT_MAGENTA}{'='*width}")
    print(f"{title}")
    print(f"{'='*width}{Colors.RESET}")

def print_subheader(title: str, width: int = 60):
    """Print colored subheader"""
    print(f"\n{Colors.BRIGHT_CYAN}{'-'*width}")
    print(f"{title}")
    print(f"{'-'*width}{Colors.RESET}")

def print_section(title: str):
    """Print section separator"""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_WHITE}{title}{Colors.RESET}")

def colored_text(text: str, color: str) -> str:
    """Return text wrapped in color codes"""
    return f"{color}{text}{Colors.RESET}"

# Convenience functions for common patterns
def success(message: str) -> str:
    """Return success text with color and emoji"""
    return f"{Colors.BRIGHT_GREEN}{Emoji.SUCCESS} {message}{Colors.RESET}"

def error(message: str) -> str:
    """Return error text with color and emoji"""  
    return f"{Colors.BRIGHT_RED}{Emoji.ERROR} {message}{Colors.RESET}"

def warning(message: str) -> str:
    """Return warning text with color and emoji"""
    return f"{Colors.BRIGHT_YELLOW}{Emoji.WARNING} {message}{Colors.RESET}"

def info(message: str) -> str:
    """Return info text with color and emoji"""
    return f"{Colors.BRIGHT_CYAN}{Emoji.INFO} {message}{Colors.RESET}"

def highlight(text: str) -> str:
    """Return highlighted text"""
    return f"{Colors.BRIGHT_YELLOW}{text}{Colors.RESET}"

def bold(text: str) -> str:
    """Return bold text"""
    return f"{Colors.BOLD}{text}{Colors.RESET}"