import time
import threading
from queue import Queue, Empty
from datetime import datetime

import psutil
from pyfiglet import Figlet

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.live import Live
import subprocess

console = Console()
figlet = Figlet(font="big")

logs = [
    "[bold cyan]Mini Console Ready[/bold cyan]",
    "Commands: hello, time, cpu, ram, clear, exit",
]

command_queue = Queue()
running = True

current_input = ""

layout = Layout()
layout.split_column(
    Layout(name="clock", ratio=3),
    Layout(name="console", ratio=1),
)


def add_log(text: str) -> None:
    logs.append(text)


def make_clock() -> Panel:
    now = datetime.now().strftime("%H:%M:%S")
    now = now.replace(":", " : ")
    big_text = figlet.renderText(now)
    return Panel(
        Align.center(f"[bold white]{big_text}[/bold white]", vertical="middle"),
        title="Clock",
        border_style="white",
    )


def make_console() -> Panel:
    # 최근 로그
    content = "\n".join(logs[-10:])

    # 입력 줄 추가
    content += f"\n[bold green]>> {current_input}[/bold green]"

    return Panel(content, title="Console", border_style="cyan")


def refresh_layout() -> None:
    layout["clock"].update(make_clock())
    layout["console"].update(make_console())


def input_worker() -> None:
    global running, current_input

    while running:
        try:
            current_input = ""  # 초기화
            cmd = console.input("")  # 프롬프트 제거
            command_queue.put(cmd)
        except (EOFError, KeyboardInterrupt):
            command_queue.put("exit")
            break

def handle_command(cmd: str) -> bool:
    cmd = cmd.strip()

    if not cmd:
        return True

    add_log(f"[bold green]> {cmd}[/bold green]")

    if cmd == "exit":
        add_log("[red]Exiting...[/red]")
        return False

    if cmd == "clear":
        logs.clear()
        logs.append("[yellow]Console cleared.[/yellow]")
        return True

    if cmd == "hello":
        add_log("Hello World!")
        return True

    if cmd == "time":
        add_log(datetime.now().strftime("Current time: %Y-%m-%d %H:%M:%S"))
        return True

    if cmd == "cpu":
        add_log(f"CPU Usage: {psutil.cpu_percent()}%")
        return True

    if cmd == "ram":
        mem = psutil.virtual_memory()
        add_log(
            f"RAM Usage: {mem.percent}% "
            f"({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)"
        )
        return True

    # add_log(f"[red]Unknown command:[/red] {cmd}")
    # return True
    else:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            output = result.stdout.strip() or result.stderr.strip()

            if not output:
                output = "[dim](no output)[/dim]"

            for line in output.splitlines():
                add_log(line)

        except Exception as e:
            add_log(f"[red]Error:[/red] {e}")

    return True

def main() -> None:
    global running

    thread = threading.Thread(target=input_worker, daemon=True)
    thread.start()

    with Live(layout, refresh_per_second=4, screen=False):
        while running:
            refresh_layout()

            try:
                while True:
                    cmd = command_queue.get_nowait()
                    running = handle_command(cmd)
                    if not running:
                        break
            except Empty:
                pass

            time.sleep(0.1)

    console.print("[bold red]Program ended.[/bold red]")


if __name__ == "__main__":
    main()