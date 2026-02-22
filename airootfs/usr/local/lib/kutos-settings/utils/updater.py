"""System update runner — detects and runs available package managers."""

import shutil
import subprocess


PACKAGE_MANAGERS = [
    ("pacman", ["sudo", "pacman", "-Syu", "--noconfirm"]),
    ("yay", ["yay", "-Syu", "--noconfirm"]),
    ("paru", ["paru", "-Syu", "--noconfirm"]),
]


def run_system_update(output_callback, done_callback):
    """Run system update using all available package managers.

    *output_callback(line: str)* — called for each output line (from any thread).
    *done_callback(success: bool)* — called when all managers finish.
    """
    overall_success = True

    for name, cmd in PACKAGE_MANAGERS:
        if name != "pacman" and shutil.which(name) is None:
            continue

        output_callback(f"\n{'='*50}\n")
        output_callback(f"  Running: {' '.join(cmd)}\n")
        output_callback(f"{'='*50}\n\n")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            for line in iter(process.stdout.readline, ""):
                output_callback(line)

            process.wait()

            if process.returncode != 0:
                output_callback(f"\n⚠ {name} exited with code {process.returncode}\n")
                overall_success = False
            else:
                output_callback(f"\n✓ {name} completed successfully.\n")

        except FileNotFoundError:
            output_callback(f"\n⚠ {name} not found, skipping.\n")
        except Exception as e:
            output_callback(f"\n✗ Error running {name}: {e}\n")
            overall_success = False

    done_callback(overall_success)
