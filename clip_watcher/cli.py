"""
Command line interface for Clip Watcher.
"""

import sys
import time
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table

from .config import WatcherConfig
from .pipeline import WatcherPipeline
from .spike_detector import SpikeDetector
from .clipper import StreamClipper
from .whisper_transcriber import WhisperTranscriber

console = Console()


@click.group()
def cli():
    """Clip Watcher: Autonomous live stream highlight clipper."""
    pass


@cli.command()
@click.option("--channel", "-c", required=True, help="Twitch channel username to watch.")
@click.option("--output-dir", "-o", default="clips", help="Directory where clips are saved.")
@click.option("--multiplier", "-m", default=3.0, type=float, help="Spike threshold multiplier vs baseline (default: 3.0x).")
@click.option("--min-messages", default=2, type=int, help="Minimum messages in window to qualify as a spike (default: 2).")
@click.option("--pre-roll", default=30, type=int, help="Pre-roll seconds to capture prior to chat reaction (default: 30s).")
@click.option("--duration", "-d", default=45, type=int, help="Clip length in seconds (default: 45s).")
def watch(channel: str, output_dir: str, multiplier: float, min_messages: int, pre_roll: int, duration: int):
    """Start autonomous stream recording and reaction-triggered clipping."""
    config = WatcherConfig(
        channel=channel,
        clips_dir=Path(output_dir),
        spike_multiplier=multiplier,
        min_spike_messages=min_messages,
        pre_roll_seconds=pre_roll,
        clip_duration_seconds=duration,
    )
    
    console.print(f"[bold green]Starting Clip Watcher for channel:[/bold green] [cyan]{channel}[/cyan]")
    console.print(f"[dim]Clips directory: {config.clips_dir}[/dim]")
    console.print(f"[dim]Spike multiplier: {multiplier}x | Min messages: {min_messages} | Pre-roll: {pre_roll}s | Duration: {duration}s[/dim]")
    console.print("[yellow]Press Ctrl+C to stop.[/yellow]")

    pipeline = WatcherPipeline(config)
    pipeline.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold red]Shutting down Clip Watcher...[/bold red]")
        pipeline.stop()


@cli.command()
@click.option("--log-file", "-l", default="chat.log", help="Path to chat.log file.")
@click.option("--multiplier", "-m", default=3.0, type=float, help="Spike multiplier (default: 3.0x).")
@click.option("--window", "-w", default=10, type=int, help="Detection window in seconds (default: 10s).")
def analyze(log_file: str, multiplier: float, window: int):
    """Analyze chat.log to identify high-velocity reaction spikes."""
    log_path = Path(log_file)
    if not log_path.exists():
        console.print(f"[bold red]Error:[/bold red] Log file '{log_file}' not found.")
        sys.exit(1)

    spikes = SpikeDetector.parse_log_file(str(log_path), window_seconds=window, multiplier=multiplier)
    
    if not spikes:
        console.print(f"[yellow]No spikes exceeding {multiplier}x baseline found in {log_file}.[/yellow]")
        return

    table = Table(title=f"Chat Reaction Spikes ({multiplier}x Threshold)")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Window Rate (msg/s)", justify="right")
    table.add_column("Baseline Rate (msg/s)", justify="right")
    table.add_column("Spike Ratio", justify="right", style="bold green")

    for s in spikes:
        table.add_row(
            s["timestamp"],
            str(s["recent_rate"]),
            str(s["baseline_rate"]),
            f"{s['ratio']}x",
        )

    console.print(table)


@cli.command()
@click.option("--stream", "-s", default="stream.ts", help="Path to recorded stream file.")
@click.option("--start", type=float, required=True, help="Start offset in seconds.")
@click.option("--duration", "-d", default=45.0, type=float, help="Clip duration in seconds.")
@click.option("--output", "-o", default="clip.mp4", help="Output MP4 file path.")
def cut(stream: str, start: float, duration: float, output: str):
    """Cut a highlight segment from stream file using FFmpeg."""
    clipper = StreamClipper()
    res = clipper.cut_clip(Path(stream), start_seconds=start, duration_seconds=duration, output_path=Path(output))
    console.print(f"[bold green]Clip extracted successfully:[/bold green] {res}")


@cli.command()
@click.option("--clip", "-c", required=True, help="Path to MP4 clip.")
@click.option("--model", "-m", default="ggml-medium.en.bin", help="Whisper model path or identifier.")
def transcribe(clip: str, model: str):
    """Transcribe audio with Whisper and burn subtitles."""
    transcriber = WhisperTranscriber(model_name=model)
    clip_path = Path(clip)
    srt = transcriber.transcribe(clip_path)
    if not srt:
        console.print("[bold red]Transcription failed or whisper-cli not installed.[/bold red]")
        return
    
    captioned = clip_path.with_name(f"{clip_path.stem}_captioned.mp4")
    transcriber.burn_subtitles(clip_path, srt, captioned)
    console.print(f"[bold green]Captions burned successfully:[/bold green] {captioned}")


if __name__ == "__main__":
    cli()
