"""
Prompt Toolkit Console Implementation

Replaces Rich console with prompt_toolkit for reliable input handling
and excellent terminal formatting without input visibility issues.
"""

import os
import sys
from typing import Optional, Any, Dict, List
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError


class PromptConsole:
    """
    Console implementation using prompt_toolkit for reliable input handling
    
    Provides Rich-like functionality but with robust input handling that
    doesn't suffer from the backspace visibility bug.
    """
    
    def __init__(self, **kwargs):
        self.style = Style.from_dict({
            'title': '#00aa00 bold',
            'subtitle': '#0000aa bold', 
            'text': '',
            'dim': '#808080',
            'success': '#00aa00',
            'warning': '#ff8800',
            'error': '#ff0000 bold',
            'cyan': '#00aaaa',
            'blue': '#0000ff',
            'green': '#00aa00',
            'yellow': '#ffff00',
            'red': '#ff0000',
            'bold': 'bold',
            'italic': 'italic'
        })
    
    def print(self, *values, style: Optional[str] = None, end: str = '\n', **kwargs):
        """Print formatted text with optional styling"""
        text = ' '.join(str(v) for v in values)
        
        if style and style in self.style.style_rules:
            # Use predefined styles
            formatted_text = FormattedText([(style, text)])
            print_formatted_text(formatted_text, style=self.style, end=end)
        else:
            # Fall back to plain text
            print(text, end=end)
    
    def input(self, message: str = "", **kwargs) -> str:
        """Get user input with reliable visibility"""
        try:
            # Use prompt_toolkit's robust input handling
            return prompt(message, style=self.style)
        except (KeyboardInterrupt, EOFError):
            return ""
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get yes/no confirmation from user"""
        suffix = " (Y/n): " if default else " (y/N): "
        try:
            response = prompt(message + suffix, style=self.style).strip().lower()
            if not response:
                return default
            return response in ['y', 'yes', 'true', '1']
        except (KeyboardInterrupt, EOFError):
            return default
    
    def choose(self, message: str, choices: List[str], default: Optional[str] = None) -> str:
        """Get user choice from a list of options"""
        completer = WordCompleter(choices)
        
        choice_text = ", ".join(choices)
        if default:
            full_message = f"{message} ({choice_text}) [{default}]: "
        else:
            full_message = f"{message} ({choice_text}): "
        
        try:
            response = prompt(full_message, completer=completer, style=self.style).strip()
            if not response and default:
                return default
            if response in choices:
                return response
            # If invalid choice, try again
            self.print(f"Invalid choice. Please select from: {choice_text}", style='warning')
            return self.choose(message, choices, default)
        except (KeyboardInterrupt, EOFError):
            return default or choices[0]


class StyledText:
    """Helper class for styled text formatting"""
    
    def __init__(self, text: str, style: str = ''):
        self.text = text
        self.style = style
    
    def __str__(self):
        return self.text
    
    @classmethod
    def bold(cls, text: str):
        return cls(text, 'bold')
    
    @classmethod
    def cyan(cls, text: str):
        return cls(text, 'cyan')
    
    @classmethod
    def green(cls, text: str):
        return cls(text, 'green')
    
    @classmethod
    def yellow(cls, text: str):
        return cls(text, 'yellow')
    
    @classmethod
    def red(cls, text: str):
        return cls(text, 'red')
    
    @classmethod
    def dim(cls, text: str):
        return cls(text, 'dim')


class Table:
    """Simple table implementation using prompt_toolkit"""
    
    def __init__(self, title: str = "", show_header: bool = True):
        self.title = title
        self.show_header = show_header
        self.columns = []
        self.rows = []
        self.column_styles = {}
    
    def add_column(self, header: str, style: str = 'text', width: Optional[int] = None):
        """Add a column to the table"""
        self.columns.append({
            'header': header,
            'style': style,
            'width': width or len(header)
        })
    
    def add_row(self, *values):
        """Add a row to the table"""
        self.rows.append(list(values))
    
    def render(self, console: PromptConsole):
        """Render the table to the console"""
        if self.title:
            console.print(f"\n{self.title}", style='bold')
            console.print("=" * len(self.title))
        
        if not self.columns:
            return
        
        # Calculate column widths
        widths = []
        for i, col in enumerate(self.columns):
            max_width = len(col['header'])
            for row in self.rows:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            widths.append(max_width + 2)  # Add padding
        
        # Render header
        if self.show_header:
            header_parts = []
            for i, col in enumerate(self.columns):
                header_parts.append(col['header'].ljust(widths[i]))
            console.print("".join(header_parts), style='bold')
            console.print("-" * sum(widths))
        
        # Render rows
        for row in self.rows:
            row_parts = []
            for i, col in enumerate(self.columns):
                value = str(row[i]) if i < len(row) else ""
                row_parts.append(value.ljust(widths[i]))
            console.print("".join(row_parts))
        
        console.print("")  # Empty line after table


class Panel:
    """Simple panel implementation"""
    
    def __init__(self, content: str, title: str = "", border_style: str = ""):
        self.content = content
        self.title = title
        self.border_style = border_style
    
    def render(self, console: PromptConsole):
        """Render the panel to the console"""
        lines = self.content.strip().split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        
        if self.title:
            max_width = max(max_width, len(self.title) + 4)
        
        # Top border
        if self.title:
            console.print(f"┌─ {self.title} " + "─" * (max_width - len(self.title) - 3) + "┐")
        else:
            console.print("┌" + "─" * (max_width + 2) + "┐")
        
        # Content
        for line in lines:
            console.print(f"│ {line.ljust(max_width)} │")
        
        # Bottom border
        console.print("└" + "─" * (max_width + 2) + "┘")


class Progress:
    """Simple progress indicator"""
    
    def __init__(self, console: PromptConsole):
        self.console = console
        self.tasks = {}
        self.task_counter = 0
    
    def add_task(self, description: str, total: Optional[int] = None):
        """Add a progress task"""
        task_id = self.task_counter
        self.task_counter += 1
        self.tasks[task_id] = {
            'description': description,
            'total': total,
            'completed': 0
        }
        return task_id
    
    def update(self, task_id: int, completed: float):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] = completed
            task = self.tasks[task_id]
            
            if task['total']:
                percentage = (completed / task['total']) * 100
                self.console.print(f"\r{task['description']}: {percentage:.0f}%", end="")
            else:
                self.console.print(f"\r{task['description']}: {completed:.0f}", end="")
    
    def remove_task(self, task_id: int):
        """Remove a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.console.print("")  # New line when done


# Factory functions for easy usage
def create_console() -> PromptConsole:
    """Create a new prompt console instance"""
    return PromptConsole()


def create_table(title: str = "", show_header: bool = True) -> Table:
    """Create a new table instance"""
    return Table(title=title, show_header=show_header)


def create_panel(content: str, title: str = "", border_style: str = "") -> Panel:
    """Create a new panel instance"""
    return Panel(content=content, title=title, border_style=border_style)


# Test function
def test_prompt_console():
    """Test the prompt console implementation"""
    console = create_console()
    
    console.print("Testing Prompt Console", style='bold')
    console.print("=" * 25)
    
    # Test styled output
    console.print("Success message", style='green')
    console.print("Warning message", style='yellow') 
    console.print("Error message", style='red')
    console.print("Dim text", style='dim')
    
    # Test table
    table = create_table("Test Table", show_header=True)
    table.add_column("Name", style='cyan')
    table.add_column("Value", style='green')
    table.add_row("Item 1", "Value 1")
    table.add_row("Item 2", "Value 2")
    table.render(console)
    
    # Test panel
    panel = create_panel("This is panel content\nWith multiple lines", title="Test Panel")
    panel.render(console)
    
    console.print("\nPrompt console test completed!", style='green')


if __name__ == "__main__":
    test_prompt_console()