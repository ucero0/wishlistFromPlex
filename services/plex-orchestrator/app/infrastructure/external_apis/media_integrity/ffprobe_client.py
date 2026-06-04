"""ffprobe-based rapid media integrity probe."""
import logging
import os
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FfprobeFileProbeResult:
    path: str
    is_valid: bool
    error: str | None = None


class FfprobeMediaIntegrityClient:
    """
    Quick container check: ffprobe must parse the file without decode.

    Uses ``ffprobe -v error`` so broken/truncated downloads fail fast before Plex ingest.
    """

    def __init__(
        self,
        *,
        ffprobe_bin: str = "ffprobe",
        timeout_seconds: int = 60,
        min_file_bytes: int = 1024,
    ):
        self._ffprobe_bin = ffprobe_bin
        self._timeout_seconds = timeout_seconds
        self._min_file_bytes = min_file_bytes

    def probe_connection(self) -> tuple[bool, str | None]:
        try:
            completed = subprocess.run(
                [self._ffprobe_bin, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            return False, f"{self._ffprobe_bin} not found on PATH"
        except subprocess.TimeoutExpired:
            return False, f"{self._ffprobe_bin} -version timed out"
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[:200]
            return False, detail or f"{self._ffprobe_bin} exited {completed.returncode}"
        return True, None

    def verify_file(self, path: str) -> FfprobeFileProbeResult:
        if not os.path.isfile(path):
            return FfprobeFileProbeResult(path, False, "not a file")
        try:
            size = os.path.getsize(path)
        except OSError as exc:
            return FfprobeFileProbeResult(path, False, str(exc))
        if size < self._min_file_bytes:
            return FfprobeFileProbeResult(
                path,
                False,
                f"file too small ({size} bytes)",
            )

        try:
            completed = subprocess.run(
                [
                    self._ffprobe_bin,
                    "-v",
                    "error",
                    "-hide_banner",
                    "-show_format",
                    "-show_streams",
                    "-select_streams",
                    "v:0",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return FfprobeFileProbeResult(
                path,
                False,
                f"ffprobe timed out after {self._timeout_seconds}s",
            )
        except FileNotFoundError:
            return FfprobeFileProbeResult(
                path,
                False,
                f"{self._ffprobe_bin} not found",
            )

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            return FfprobeFileProbeResult(
                path,
                False,
                detail[:500] if detail else f"ffprobe exit {completed.returncode}",
            )

        if "codec_name=" not in (completed.stdout or ""):
            return FfprobeFileProbeResult(path, False, "no video stream found")

        return FfprobeFileProbeResult(path, True, None)

    def verify_files(self, paths: list[str]) -> list[FfprobeFileProbeResult]:
        results: list[FfprobeFileProbeResult] = []
        for path in paths:
            result = self.verify_file(path)
            results.append(result)
            if not result.is_valid:
                logger.warning(
                    "Media integrity failed for %s: %s", path, result.error
                )
        return results
