"""
Rich terminal logging with colored output for LinkedInMaxx backend.
Provides visual feedback for agent actions, data publishing, and task processing.
"""

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import logging
from datetime import datetime
from typing import Optional

# Create console for rich output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger("linkedinmaxx")


class TerminalFeedback:
    """Provides colored terminal feedback for agent actions and data operations."""
    
    @staticmethod
    def agent_action(agent_name: str, action: str, details: Optional[str] = None):
        """Display agent action with colored output."""
        text = Text()
        text.append(f"🤖 [{agent_name}] ", style="bold cyan")
        text.append(action, style="bold white")
        if details:
            text.append(f"\n   {details}", style="dim white")
        
        console.print(Panel(text, border_style="cyan", title="Agent Action"))
    
    @staticmethod
    def data_published(queue_name: str, data_type: str, data: dict):
        """Display data published to queue."""
        text = Text()
        text.append("📤 PUBLISHED: ", style="bold green")
        text.append(f"{data_type} to {queue_name}\n", style="white")
        text.append(f"   {str(data)[:100]}...", style="dim white")
        
        console.print(Panel(text, border_style="green", title="Data Published"))
    
    @staticmethod
    def data_extracted(source: str, data_type: str, count: int = 1):
        """Display data extraction results."""
        text = Text()
        text.append("📥 EXTRACTED: ", style="bold blue")
        text.append(f"{count} {data_type}(s) from {source}", style="white")
        
        console.print(Panel(text, border_style="blue", title="Data Extracted"))
    
    @staticmethod
    def task_queued(task_type: str, task_id: str):
        """Display task queued message."""
        console.print(f"⏳ [yellow]Queued[/yellow] {task_type} [dim](ID: {task_id})[/dim]")
    
    @staticmethod
    def task_processing(task_type: str, task_id: str):
        """Display task processing message."""
        console.print(f"⚙️  [cyan]Processing[/cyan] {task_type} [dim](ID: {task_id})[/dim]")
    
    @staticmethod
    def task_completed(task_type: str, task_id: str, result: Optional[str] = None):
        """Display task completion message."""
        text = f"✅ [green]Completed[/green] {task_type} [dim](ID: {task_id})[/dim]"
        if result:
            text += f"\n   {result}"
        console.print(text)
    
    @staticmethod
    def error(message: str, error: Optional[Exception] = None):
        """Display error message."""
        text = Text()
        text.append("❌ ERROR: ", style="bold red")
        text.append(message, style="white")
        if error:
            text.append(f"\n   {str(error)}", style="dim red")
        
        console.print(Panel(text, border_style="red", title="Error"))
    
    @staticmethod
    def instruction_for_playwright(action: str, instruction: dict):
        """Display instruction published for Playwright."""
        table = Table(title=f"🎭 Playwright Instruction: {action}", show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in instruction.items():
            table.add_row(str(key), str(value)[:50])
        
        console.print(table)
    
    @staticmethod
    def agent_classification(profile_url: str, category: str, confidence: Optional[float] = None):
        """Display profile classification result."""
        text = Text()
        text.append("🏷️  CLASSIFIED: ", style="bold yellow")
        text.append(f"{profile_url[:50]}...\n", style="white")
        text.append(f"   Category: {category}", style="bold white")
        if confidence:
            text.append(f" (confidence: {confidence:.2%})", style="dim white")
        
        console.print(Panel(text, border_style="yellow", title="Classification"))


# Create global instance
feedback = TerminalFeedback()

