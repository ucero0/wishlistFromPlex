#!/usr/bin/env python3
"""
Simple HTTP server for ClamAV + YARA scanning
Runs in ClamAV container and provides HTTP API for scanning
"""
import json
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Optional
import sys

# YARA rules path in ClamAV container
YARA_RULES_PATH = "/yara-rules"
PORT = 3311  # Different from ClamAV daemon port (3310)


from typing import Tuple, Optional

def scan_with_clamav(file_path: str) -> Tuple[bool, Optional[str]]:
    """Scan file with ClamAV using clamdscan."""
    try:
        result = subprocess.run(
            ["clamdscan", "--no-summary", file_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 1:
            output = result.stdout.strip()
            if "FOUND" in output:
                parts = output.split(":")
                if len(parts) > 1:
                    virus_part = parts[1].strip()
                    virus_name = virus_part.replace("FOUND", "").strip()
                    return True, virus_name
                return True, "Unknown"
        return False, None
    except Exception:
        return False, None


def scan_with_yara(file_path: str) -> list[str]:
    """Scan file with YARA rules."""
    matches = []
    try:
        if subprocess.run(["which", "yara"], capture_output=True).returncode != 0:
            return matches
        
        rules_path = os.path.join(YARA_RULES_PATH)
        if not os.path.exists(rules_path):
            return matches
        
        # Find all YARA rule files recursively
        yara_files = []
        for root, dirs, files in os.walk(rules_path):
            for file in files:
                if file.endswith(('.yar', '.yara')):
                    yara_files.append(os.path.join(root, file))
        
        for rule_file in yara_files:
            try:
                result = subprocess.run(
                    ["yara", "-s", rule_file, file_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            rule_name = line.split()[0] if line.split() else ""
                            if rule_name and rule_name not in matches:
                                matches.append(rule_name)
            except Exception:
                continue
    except Exception:
        pass
    
    return matches


def scan_file(file_path: str) -> dict:
    """Scan a single file."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}", "is_infected": False}
    
    is_infected, virus_name = scan_with_clamav(file_path)
    yara_matches = scan_with_yara(file_path)
    
    if yara_matches:
        is_infected = True
    
    return {
        "is_infected": is_infected,
        "virus_name": virus_name,
        "yara_matches": yara_matches,
        "file_path": file_path
    }


def scan_directory(directory_path: str) -> dict:
    """Scan all files in a directory."""
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return {"error": f"Directory not found: {directory_path}", "is_infected": False}
    
    scanned_files = []
    infected_files = []
    all_virus_names = []
    all_yara_matches = []
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            scanned_files.append(file_path)
            
            result = scan_file(file_path)
            if result.get("is_infected"):
                infected_files.append(file_path)
                if result.get("virus_name"):
                    all_virus_names.append(result["virus_name"])
                all_yara_matches.extend(result.get("yara_matches", []))
    
    return {
        "is_infected": len(infected_files) > 0,
        "virus_name": all_virus_names[0] if all_virus_names else None,
        "yara_matches": list(set(all_yara_matches)),
        "scanned_files": scanned_files,
        "infected_files": infected_files
    }


class ScanHandler(BaseHTTPRequestHandler):
    """HTTP request handler for scanning API."""
    
    def do_GET(self):
        """Handle GET requests - health check."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests - scan files."""
        if self.path != "/scan":
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            path = data.get("path")
            
            if not path:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No path provided"}).encode())
                return
            
            # Determine if file or directory
            if os.path.isfile(path):
                result = scan_file(path)
            elif os.path.isdir(path):
                result = scan_directory(path)
            else:
                result = {"error": f"Path not found: {path}"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    """Start the HTTP server."""
    server = HTTPServer(("0.0.0.0", PORT), ScanHandler)
    print(f"Scan service listening on port {PORT}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()

