"""
Terminal Input Handler

Provides robust input handling across different terminal environments.
"""

import os
import sys
import termios
import tty
import select
import subprocess
from typing import Optional, Any
from .prompt_console import PromptConsole


class TerminalInputHandler:
    """
    Handles terminal input with proper echo visibility
    
    Default behavior: Uses 'rich_fixed' method for most TTY environments to ensure
    input visibility and fix Rich console backspace bug. Falls back to 'simple' 
    for dumb terminals and 'force_echo' for pure screen environments.
    """
    
    def __init__(self, console: Optional[PromptConsole] = None):
        self.console = console or PromptConsole()
        self.debug = os.getenv('DEBUG_INPUT', 'false').lower() == 'true'
        self.is_tty = sys.stdin.isatty()
        self.platform = sys.platform
        
    def get_input(self, prompt_text: str, method: Optional[str] = None) -> str:
        """
        Get user input with automatic method selection and fallbacks
        
        Args:
            prompt_text: The prompt to display
            method: Specific method to use, or None for auto-detection
            
        Returns:
            User input string
        """
        if method is None:
            method = self._detect_best_method()
        
        if self.debug:
            self.console.print(f"Input method: {method}, TTY: {self.is_tty}", style='dim')
        
        # Temporarily suppress logging to prevent interference
        import logging
        root_logger = logging.getLogger()
        original_level = root_logger.level
        root_logger.setLevel(logging.CRITICAL)
        
        # Try primary method first
        try:
            response = self._get_input_with_method(prompt_text, method)
            
            # Show feedback for what was captured (helps with invisible input)
            if response and not self.debug:
                self.console.print(f"→ {response}", style='dim')
            elif self.debug:
                self.console.print(f"Captured: '{response}' (len: {len(response)})", style='dim')
            
            return response
            
        except Exception as e:
            if self.debug:
                self.console.print(f"Input method {method} failed: {e}", style='error')
            
            # Try fallback methods in order
            fallback_methods = ['rich_fixed', 'readline', 'simple', 'native']
            for fallback_method in fallback_methods:
                if fallback_method != method:  # Don't retry the same method
                    try:
                        if self.debug:
                            self.console.print(f"Trying fallback: {fallback_method}", style='warning')
                        
                        response = self._get_input_with_method(prompt_text, fallback_method)
                        
                        if self.debug:
                            self.console.print(f"Fallback {fallback_method} succeeded", style='success')
                        
                        # Show feedback
                        if response and not self.debug:
                            self.console.print(f"→ {response}", style='dim')
                        
                        return response
                        
                    except Exception as fallback_e:
                        if self.debug:
                            self.console.print(f"Fallback {fallback_method} failed: {fallback_e}", style='error')
                        continue
            
            # Ultimate fallback
            return self._ultimate_fallback(prompt_text)
        
        finally:
            root_logger.setLevel(original_level)
    
    def _detect_best_method(self) -> str:
        """Detect the best input method for current environment"""
        
        # Check for environment override
        env_method = os.getenv('INPUT_METHOD', '').lower()
        if env_method in ['native', 'readline', 'rich', 'rich_fixed', 'force_echo', 'simple']:
            return env_method
        
        # Auto-detection based on environment
        if not self.is_tty:
            return 'simple'  # Non-interactive, use simple input
        
        # Check for common problematic environments
        term = os.getenv('TERM', '').lower()
        tmux = os.getenv('TMUX', '')
        ssh_client = os.getenv('SSH_CLIENT', '')
        ssh_tty = os.getenv('SSH_TTY', '')
        
        # Use rich_fixed as default for all TTY environments since it fixes input visibility
        # and has robust fallbacks built-in. Only use alternatives for specific cases.
        
        if 'dumb' in term:
            # Dumb terminal can't handle Rich formatting
            return 'simple'
        elif 'screen' in term and not tmux:
            # Pure screen (without tmux) sometimes has issues with Rich
            return 'force_echo'
        else:
            # Default to rich_fixed for all other TTY environments:
            # - Regular terminals (xterm, konsole, etc.)
            # - SSH connections
            # - tmux sessions  
            # - Linux console
            # - macOS Terminal
            # - Unknown terminals
            return 'rich_fixed'
    
    def _get_input_with_method(self, prompt_text: str, method: str) -> str:
        """Get input using specific method"""
        
        if method == 'native':
            return self._native_input(prompt_text)
        elif method == 'readline':
            return self._readline_input(prompt_text)
        elif method == 'rich':
            return self._rich_input(prompt_text)
        elif method == 'rich_fixed':
            return self._rich_fixed_input(prompt_text)
        elif method == 'force_echo':
            return self._force_echo_input(prompt_text)
        elif method == 'simple':
            return self._simple_input(prompt_text)
        else:
            raise ValueError(f"Unknown input method: {method}")
    
    def _native_input(self, prompt_text: str) -> str:
        """Native input with proper terminal setup"""
        if not self.is_tty:
            return self._simple_input(prompt_text)
        
        # Save terminal state
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Ensure echo is enabled and we're in canonical mode
            new_settings = old_settings.copy()
            new_settings[3] |= (termios.ECHO | termios.ICANON)  # Enable echo and canonical
            new_settings[3] &= ~termios.ECHOCTL  # Disable control character echo
            termios.tcsetattr(fd, termios.TCSANOW, new_settings)
            
            # Clear any pending input
            termios.tcflush(fd, termios.TCIFLUSH)
            
            # Display prompt and get input
            sys.stdout.write(prompt_text)
            sys.stdout.flush()
            
            response = sys.stdin.readline().rstrip('\n')
            return response
            
        finally:
            # Restore original terminal settings
            termios.tcsetattr(fd, termios.TCSANOW, old_settings)
    
    def _readline_input(self, prompt_text: str) -> str:
        """Input using readline module for better line editing"""
        import readline
        
        # Configure readline for better behavior
        readline.clear_history()  # Clear any existing history
        
        # Use input() with readline support
        return input(prompt_text)
    
    def _rich_input(self, prompt_text: str) -> str:
        """Input using prompt_toolkit (renamed for backwards compatibility)"""
        # Use prompt_toolkit directly for reliable input
        return self.console.input(prompt_text)
    
    def _rich_fixed_input(self, prompt_text: str) -> str:
        """Input using prompt_toolkit for reliable input handling"""
        # Use prompt_toolkit directly - this is the most reliable method
        return self.console.input(prompt_text)
    
    def _force_echo_input(self, prompt_text: str) -> str:
        """Force echo using system commands"""
        if not self.is_tty:
            return self._simple_input(prompt_text)
        
        # Use stty to force echo
        try:
            # Save current state
            result = subprocess.run(['stty', '-g'], capture_output=True, text=True, check=True)
            original_state = result.stdout.strip()
            
            # Force echo on
            subprocess.run(['stty', 'echo', 'icanon'], check=True)
            
            try:
                sys.stdout.write(prompt_text)
                sys.stdout.flush()
                response = sys.stdin.readline().rstrip('\n')
                return response
            finally:
                # Restore original state
                subprocess.run(['stty', original_state], check=True)
                
        except subprocess.CalledProcessError:
            # Fallback if stty commands fail
            return self._simple_input(prompt_text)
    
    def _simple_input(self, prompt_text: str) -> str:
        """Simple fallback input method"""
        sys.stdout.write(prompt_text)
        sys.stdout.flush()
        return input()
    
    def _fallback_input(self, prompt_text: str) -> str:
        """Ultimate fallback when all else fails"""
        return self._ultimate_fallback(prompt_text)
    
    def _ultimate_fallback(self, prompt_text: str) -> str:
        """Last resort input method"""
        try:
            # Try the most basic input possible
            print(prompt_text, end='', flush=True)
            response = input()
            return response
        except EOFError:
            # Handle EOF gracefully
            self.console.print("\nEOF detected, using empty response", style='warning')
            return ""
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            self.console.print("\nInterrupted, using empty response", style='warning')
            return ""
        except Exception as e:
            # If even this fails, return empty string
            self.console.print(f"Input failed ({e}), using empty response", style='error')
            return ""
    
    def test_input_methods(self) -> dict:
        """Test all input methods to see which work"""
        results = {}
        test_prompt = "Test prompt: "
        
        methods = ['native', 'readline', 'rich', 'rich_fixed', 'force_echo', 'simple']
        
        for method in methods:
            try:
                self.console.print(f"\nTesting {method} method...")
                self.console.print("Type 'test' and press Enter:")
                
                response = self._get_input_with_method(test_prompt, method)
                results[method] = {
                    'status': 'success',
                    'response': response,
                    'visible': response == 'test'  # Assuming user types 'test'
                }
                
            except Exception as e:
                results[method] = {
                    'status': 'failed',
                    'error': str(e),
                    'visible': False
                }
        
        return results


def create_input_handler(console: Optional[PromptConsole] = None) -> TerminalInputHandler:
    """Factory function to create input handler"""
    return TerminalInputHandler(console)


# Convenience function for quick testing
def test_terminal_input():
    """Test terminal input functionality"""
    handler = TerminalInputHandler()
    
    print("Testing terminal input methods...")
    print("For each method, type 'test' and press Enter")
    
    results = handler.test_input_methods()
    
    print("\n" + "="*50)
    print("RESULTS:")
    print("="*50)
    
    for method, result in results.items():
        status = result['status']
        if status == 'success':
            visible = "✓ VISIBLE" if result['visible'] else "✗ INVISIBLE"
            print(f"{method:12}: {status:8} - {visible} - got: '{result.get('response', '')}'")
        else:
            print(f"{method:12}: {status:8} - ERROR: {result.get('error', '')}")
    
    # Recommend best method
    working_methods = [m for m, r in results.items() if r['status'] == 'success' and r.get('visible', False)]
    if working_methods:
        print(f"\nRECOMMENDED: Use INPUT_METHOD={working_methods[0]}")
    else:
        print(f"\nWARNING: No methods provided visible input!")


if __name__ == "__main__":
    test_terminal_input()