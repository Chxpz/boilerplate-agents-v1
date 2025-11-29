#!/usr/bin/env python3
import httpx
import sys
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
import uuid
from config import settings

console = Console(width=100)


class AgentCLI:
    def __init__(self, api_url: str = None):
        self.api_url = api_url or f"http://{settings.api_host}:{settings.api_port}/api/v1"
        self.session_id = str(uuid.uuid4())[:8]
        self.client = httpx.Client(timeout=60.0)
    
    def print_banner(self):
        banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       🤖 AI Agent CLI - Interactive Session                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold cyan")
        console.print(f"  Session ID: [yellow]{self.session_id}[/yellow]", style="dim")
        console.print("  Commands: [cyan]exit[/cyan], [cyan]quit[/cyan], [cyan]clear[/cyan]\n", style="dim")
    
    def check_health(self):
        try:
            response = self.client.get(f"{self.api_url}/health")
            if response.status_code == 200:
                console.print("  ✓ Connected to agent\n", style="green")
                return True
        except Exception as e:
            console.print(f"  ✗ Cannot connect to agent: {e}", style="red")
            console.print(f"  Make sure the server is running on {self.api_url}\n", style="yellow")
            return False
    
    def send_message_stream(self, message: str):
        try:
            with self.client.stream(
                "POST",
                f"{self.api_url}/chat/stream",
                json={"message": message, "session_id": self.session_id},
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    console.print(f"\n[red]✗ Error: {response.status_code}[/red]\n")
                    return
                
                console.print("\n[bold cyan]🤖 Agent[/bold cyan]")
                console.print("─" * 80, style="dim")
                
                first_chunk_received = False
                spinner = None
                word_buffer = []
                char_count = 0
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        if not first_chunk_received:
                            first_chunk_received = True
                        
                        data = json.loads(line[6:])
                        if "error" in data:
                            console.print(f"\n[red]✗ {data['error']}[/red]\n")
                            return
                        
                        chunk = data.get("chunk", "")
                        word_buffer.append(chunk)
                        char_count += 1
                        
                        # Print word by word for natural flow
                        if chunk in [" ", "\n"]:
                            word = "".join(word_buffer)
                            console.print(word, end="", style="bright_green")
                            word_buffer = []
                        
                        # After 50 chars, speed up
                        elif char_count > 50:
                            console.print(chunk, end="", style="bright_green")
                            word_buffer = []
                
                if word_buffer:
                    console.print("".join(word_buffer), end="", style="bright_green")
                
                console.print("\n" + "─" * 80, style="dim")
                console.print()
            
        except Exception as e:
            console.print(f"\n[red]✗ Error: {str(e)}[/red]\n")
    
    def run(self):
        self.print_banner()
        
        if not self.check_health():
            sys.exit(1)
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]💬 You[/bold blue]")
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    console.print("\n[yellow]👋 Ending session...[/yellow]\n")
                    break
                
                if user_input.lower() == 'clear':
                    console.clear()
                    self.print_banner()
                    continue
                
                if not user_input.strip():
                    continue
                
                self.send_message_stream(user_input)
                
            except KeyboardInterrupt:
                console.print("\n\n[yellow]⚠️  Session interrupted[/yellow]\n")
                break
            except Exception as e:
                console.print(f"\n[red]✗ Error: {e}[/red]\n")
        
        self.client.close()
        console.print("[cyan]Goodbye! 👋[/cyan]\n")


def main():
    cli = AgentCLI()
    cli.run()


if __name__ == "__main__":
    main()
