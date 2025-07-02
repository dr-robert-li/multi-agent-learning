"""
Fixed Rich Console Implementation

Workaround for Rich console input backspace bug (issue #2293)
https://github.com/Textualize/rich/issues/2293
"""

import os
import sys
from getpass import getpass
from typing import Optional, TextIO, Any
from rich.console import Console
from rich.text import Text


class FixedConsole(Console):
    """
    Console subclass that fixes the input backspace bug in Rich >= 12.0.0
    
    The bug: When using console.input() and backspacing over input, the prompt
    itself is also erased. This happens due to how Rich handles prompt and
    input line rendering with the readline module.
    
    The fix: Separate prompt rendering from input capture, using getpass for
    password input and falling back to built-in input() for regular input.
    """
    
    def input(
        self,
        prompt: Any = "",
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: Optional[TextIO] = None
    ) -> str:
        """
        Override input method to fix backspace bug
        
        Args:
            prompt: The prompt to display
            markup: Whether to process Rich markup in prompt
            emoji: Whether to process emoji in prompt
            password: Whether this is password input (hidden)
            stream: Optional input stream
            
        Returns:
            User input string
        """
        # Handle empty prompt
        if not prompt:
            prompt = ""
        
        # Render prompt separately to avoid readline interference
        prompt_str = ""
        if prompt:
            # Use Rich's capture to render the prompt with markup/emoji
            with self.capture() as capture:
                self.print(prompt, markup=markup, emoji=emoji, end="")
                prompt_str = capture.get()
        
        # Handle legacy Windows console
        if self.legacy_windows:
            self.file.write(prompt_str)
            prompt_str = ""
        
        # Get input based on type
        if password:
            # Use getpass for password input (hides input)
            result = getpass(prompt_str, stream=stream)
        else:
            # For regular input, use separate approaches based on stream
            if stream:
                # If stream is provided, write prompt and read from stream
                self.file.write(prompt_str)
                result = stream.readline()
                if result.endswith('\n'):
                    result = result[:-1]  # Remove trailing newline
            else:
                # Use built-in input() with rendered prompt
                # This avoids Rich's readline interference
                result = input(prompt_str)
        
        return result
    
    def print_and_input(self, prompt: Any = "", **kwargs) -> str:
        """
        Alternative method that completely separates print and input
        
        This method explicitly prints the prompt first, then gets input
        without any prompt, ensuring complete separation.
        """
        # Print the prompt
        if prompt:
            self.print(prompt, end="")
        
        # Get input without prompt
        return input()


class SafeConsole(FixedConsole):
    """
    Enhanced console with additional safety features and fallbacks
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debug_input = os.getenv('DEBUG_RICH_INPUT', 'false').lower() == 'true'
        self.fallback_enabled = True
    
    def safe_input(
        self,
        prompt: Any = "",
        fallback_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Safe input with automatic fallback if Rich input fails
        
        Args:
            prompt: Rich-formatted prompt
            fallback_prompt: Plain text fallback prompt
            **kwargs: Additional arguments for input()
            
        Returns:
            User input string
        """
        if fallback_prompt is None:
            # Create plain text version of prompt
            if hasattr(prompt, '__str__'):
                fallback_prompt = str(prompt)
            else:
                fallback_prompt = ""
        
        try:
            # Try Rich input first
            if self.debug_input:
                self.print(f"[dim]Trying Rich input method...[/dim]")
            
            result = self.input(prompt, **kwargs)
            
            if self.debug_input:
                self.print(f"[dim]Rich input successful: '{result}'[/dim]")
            
            return result
            
        except Exception as e:
            if self.debug_input:
                self.print(f"[yellow]Rich input failed ({e}), using fallback...[/yellow]")
            
            if not self.fallback_enabled:
                raise
            
            # Fallback to basic input
            try:
                # Print fallback prompt
                if fallback_prompt:
                    print(fallback_prompt, end="", flush=True)
                
                result = input()
                
                if self.debug_input:
                    self.print(f"[dim]Fallback input successful: '{result}'[/dim]")
                
                return result
                
            except Exception as fallback_e:
                if self.debug_input:
                    self.print(f"[red]Fallback input also failed: {fallback_e}[/red]")
                
                # Ultimate fallback
                return ""


def create_fixed_console(**kwargs) -> FixedConsole:
    """Factory function to create fixed console instance"""
    return FixedConsole(**kwargs)


def create_safe_console(**kwargs) -> SafeConsole:
    """Factory function to create safe console instance"""
    return SafeConsole(**kwargs)


# Test function to verify the fix works
def test_console_fix():
    """Test the console fix"""
    print("Testing Rich console input fix...")
    
    console = FixedConsole()
    
    try:
        print("\nTest 1: Regular input")
        response1 = console.input("Enter some text (try backspacing): ")
        print(f"Got: '{response1}'")
        
        print("\nTest 2: Rich markup input")
        response2 = console.input("[bold cyan]Enter text with markup[/bold cyan]: ")
        print(f"Got: '{response2}'")
        
        print("\nTest 3: Safe input with fallback")
        safe_console = SafeConsole(debug_input=True)
        response3 = safe_console.safe_input("[bold green]Safe input test[/bold green]: ")
        print(f"Got: '{response3}'")
        
        print("\n✅ Console fix test completed successfully!")
        
    except Exception as e:
        print(f"❌ Console fix test failed: {e}")


if __name__ == "__main__":
    test_console_fix()