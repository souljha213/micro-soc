from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from pathlib import Path
class StosCockpit(App):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("MICRO-SOC ACTIVE DEFENSE GRID\nStatus: Operational", classes="box")
        yield Footer()
if __name__ == "__main__": StosCockpit().run()
