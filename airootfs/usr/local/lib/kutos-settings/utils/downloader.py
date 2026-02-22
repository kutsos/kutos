"""Download and extract desktop environment config archives."""

import os
import tarfile
import tempfile
import requests


def download_and_extract(url, dest=None):
    """Download a .tar.gz from *url* and extract to ~/.config.

    Returns (success: bool, message: str).
    """
    if dest is None:
        dest = os.path.expanduser("~/.config")

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = tmp.name
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)

        os.makedirs(dest, exist_ok=True)

        with tarfile.open(tmp_path, "r:gz") as tar:
            tar.extractall(path=dest)

        os.unlink(tmp_path)
        return True, "Configuration installed successfully."

    except requests.ConnectionError:
        return False, "No internet connection."
    except requests.HTTPError as e:
        return False, f"Download failed: HTTP {e.response.status_code}"
    except tarfile.TarError as e:
        return False, f"Extraction failed: {e}"
    except Exception as e:
        return False, str(e)
