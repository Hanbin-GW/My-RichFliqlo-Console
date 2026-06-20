import asyncio
import os
import platform
import subprocess
from datetime import datetime

import psutil
from pyfiglet import Figlet

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual.reactive import reactive
from textual.binding import Binding

class ClockDisplay(Static):
      time_text = reactive("")

      def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.figlet_big = Figlet(font="big")
            self.figlet_standard = Figlet(font="standard") 

      def on_mount(self) -> None:
            self.update_clock()
            self.set_interval(1, self.update_clock)

      def update_clock(self) -> None:
            now = datetime.now()

            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S").replace(":", " : ")

            big_text = self.figlet_big.renderText(time_str)
            standard_date = self.figlet_standard.renderText(date_str)

            self.time_text = (
                  f"[bold cyan]{standard_date}[/bold cyan]\n"
                  f"[bold white]{big_text}[/bold white]"
            )


      def watch_time_text(self, value: str) -> None:
            self.update(value)

class MiniConsoleApp(App):
      clock_only = False
      CSS = """
      Screen {
            background: black;
            color: white;
      }

      #main-layout {
            height: 100%;
      }

      #clock {
            height: 1fr;
            content-align: center middle;
            border: solid white;
      }

      #log {
            height: 12;
            border: solid cyan;
      }

      #input {
            height: 3;
            border: solid green;
      }
      """

      BINDINGS = [
            ("ctrl+c", "quit", "Quit"),
            ("ctrl+u", "toggle_ui", "Toggle UI"),
            ("ctrl+k", "toggle_clock_mode", "Clock Mode"),
      ]

      def action_toggle_ui(self):
            header = self.query(Header)
            footer = self.query(Footer)

            for h in header:
                  h.display = not h.display

            for f in footer:
                  f.display = not f.display

      def compose(self) -> ComposeResult:
            yield Header(show_clock=False)
            with Vertical(id="main-layout"):
                  yield ClockDisplay(id="clock")
                  yield RichLog(id="log", wrap=True, markup=True, highlight=True)
                  yield Input(placeholder="Type a command and press Enter...", id="input")
            yield Footer()

      def on_mount(self) -> None:
            log = self.query_one("#log", RichLog)
            log.write("[bold cyan]Mini Console Ready[/bold cyan]")
            log.write("Commands: hello, time, cpu, ram, clear, exit")
            self.query_one("#input", Input).focus()

      async def on_input_submitted(self, event: Input.Submitted) -> None:
            cmd = event.value.strip()
            input_widget = self.query_one("#input", Input)
            log = self.query_one("#log", RichLog)

            if not cmd:
                  input_widget.value = ""
                  return

            log.write(f"[bold green]> {cmd}[/bold green]")
            input_widget.value = ""

            keep_running = await self.handle_command(cmd)
            if not keep_running:
                  await self.action_quit()

      async def handle_command(self, cmd: str) -> bool:
            log = self.query_one("#log", RichLog)

            if cmd == "exit":
                  log.write("[red]Exiting...[/red]")
                  return False

            if cmd == "clear":
                  log.clear()
                  log.write("[yellow]Console cleared.[/yellow]")
                  return True

            if cmd == "hello":
                  log.write("Hello World!")
                  return True

            if cmd == "time":
                  log.write(datetime.now().strftime("Current time: %Y-%m-%d %H:%M:%S"))
                  return True

            if cmd == "cpu":
                  log.write(f"CPU Usage: {psutil.cpu_percent()}%")
                  return True

            if cmd == "ram":
                  mem = psutil.virtual_memory()
                  log.write(
                  f"RAM Usage: {mem.percent}% "
                  f"({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)"
                  )
                  return True

            await self.run_shell_command(cmd)
            return True
      
      def action_toggle_clock_mode(self):
            self.clock_only = not self.clock_only

            header = self.query(Header)
            footer = self.query(Footer)
            log = self.query("#log")
            input_box = self.query("#input")
            clock = self.query("#clock")

            if self.clock_only:
                  for h in header:
                        h.display = False
                  for f in footer:
                        f.display = False
                  for l in log:
                        l.display = False
                  for i in input_box:
                        i.display = False

                  for c in clock:
                        c.styles.height = "100%"

            else:
                  for h in header:
                        h.display = True
                  for f in footer:
                        f.display = True
                  for l in log:
                        l.display = True
                  for i in input_box:
                        i.display = True

                  for c in clock:
                        c.styles.height = "1fr"

      async def run_shell_command(self, cmd: str) -> None:
            log = self.query_one("#log", RichLog)

            if platform.system() == "Windows":
                  shell_executable = os.environ.get("COMSPEC", "cmd.exe")
            else:
                  shell_executable = os.environ.get("SHELL", "/bin/bash")

            try:
                  process = await asyncio.create_subprocess_shell(
                  cmd,
                  stdout=asyncio.subprocess.PIPE,
                  stderr=asyncio.subprocess.PIPE,
                  executable=shell_executable if platform.system() != "Windows" else None,
                  )

                  stdout, stderr = await process.communicate()

                  out_text = stdout.decode(errors="replace").strip()
                  err_text = stderr.decode(errors="replace").strip()

                  if out_text:
                        for line in out_text.splitlines():
                              log.write(line)

                  if err_text:                        # ← out_text와 같은 레벨
                        for line in err_text.splitlines():
                              log.write(f"[red]{line}[/red]")
                  if not out_text and not err_text:
                        log.write("[dim](no output)[/dim]")

            except Exception as e:
                  log.write(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app = MiniConsoleApp()
    app.run()