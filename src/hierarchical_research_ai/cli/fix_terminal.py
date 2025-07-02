#!/usr/bin/env python3
"""
Terminal fix utility for input visibility issues
"""
import os
import sys
import subprocess


def check_terminal_state():
    """Check current terminal settings"""
    try:
        result = subprocess.run(['stty', '-a'], capture_output=True, text=True)
        print("Current terminal settings:")
        print(result.stdout)
        
        # Check if echo is enabled
        if '-echo' in result.stdout:
            print("\n⚠️  WARNING: Terminal echo is DISABLED!")
            return False
        else:
            print("\n✓ Terminal echo is enabled")
            return True
    except Exception as e:
        print(f"Could not check terminal settings: {e}")
        return None


def fix_terminal():
    """Reset terminal to sane defaults"""
    try:
        print("\nResetting terminal settings...")
        subprocess.run(['stty', 'sane'], check=True)
        subprocess.run(['stty', 'echo'], check=True)
        print("✓ Terminal settings reset")
        return True
    except Exception as e:
        print(f"❌ Failed to reset terminal: {e}")
        return False


def test_input():
    """Test if input is visible"""
    print("\n--- Input Visibility Test ---")
    print("Type something and press Enter. You should see what you type:")
    test = input("Test input: ")
    print(f"You typed: '{test}'")
    
    if test:
        print("✓ Input test successful")
    else:
        print("⚠️  No input received")


if __name__ == "__main__":
    print("=== Terminal Input Fix Utility ===\n")
    
    # Check current state
    echo_enabled = check_terminal_state()
    
    # Fix if needed
    if echo_enabled is False:
        if fix_terminal():
            test_input()
    else:
        print("\nTerminal appears to be configured correctly.")
        test_input()
    
    print("\nIf input is still not visible, try:")
    print("1. Exit any terminal multiplexers (tmux, screen)")
    print("2. Use a different terminal emulator")
    print("3. Run: export TERM=xterm-256color")