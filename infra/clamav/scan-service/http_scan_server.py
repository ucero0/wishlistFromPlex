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
        print(f"[CLAMAV] Scanning: {file_path}", file=sys.stderr, flush=True)
        result = subprocess.run(
            ["clamdscan", "--no-summary", file_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(f"[CLAMAV] Return code: {result.returncode}, Output: {result.stdout[:100]}", file=sys.stderr, flush=True)
        
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
    except subprocess.TimeoutExpired:
        print(f"[CLAMAV] Timeout scanning: {file_path}", file=sys.stderr, flush=True)
        return False, None
    except Exception as e:
        print(f"[CLAMAV] Error: {str(e)}", file=sys.stderr, flush=True)
        return False, None


def scan_with_yara(file_path: str) -> list[str]:
    """Scan file with YARA rules - optimized for media/video files.
    
    Focuses on rules most relevant to detecting malicious content in media files:
    - Packers (malware packed in containers)
    - Suspicious strings/patterns
    - Hidden executables (PE files in media containers)
    - File format anomalies
    """
    matches = []
    try:
        if subprocess.run(["which", "yara"], capture_output=True).returncode != 0:
            return matches
        
        rules_path = os.path.join(YARA_RULES_PATH)
        if not os.path.exists(rules_path):
            return matches
        
        print(f"[YARA] Starting YARA scan for: {file_path}", file=sys.stderr, flush=True)
        
        # Priority rules for media/video files - most relevant categories
        # Focus on categories that detect:
        # - Packed executables (malware in containers)
        # - Hidden files (PE files in media)
        # - Suspicious patterns
        priority_categories = [
            "packers",           # Detect malware packed in containers
            "maldocs",           # Malicious documents (may contain embedded code)
        ]
        
        # Specific rule files most relevant for media file scanning
        # Using smaller, more targeted rules to avoid performance issues
        priority_rules = [
            "packers/packer_compiler_signatures.yar",  # Detects packed executables
            "maldocs/Maldoc_Hidden_PE_file.yar",       # Detects hidden PE files in containers
            "utils/suspicious_strings.yar",            # Suspicious patterns (68KB)
            "utils/magic.yar",                          # File magic number detection
        ]
        
        yara_files = []
        
        # First, add custom rules for media files (subtitle detection, etc.)
        custom_rules_path = "/scan-service/yara-rules-custom"
        if os.path.exists(custom_rules_path):
            for root, dirs, files in os.walk(custom_rules_path):
                for file in files:
                    if file.endswith(('.yar', '.yara')):
                        custom_rule = os.path.join(root, file)
                        # Add custom rules directly (they're in a different location)
                        yara_files.append(custom_rule)
        
        # Then, add priority rule files
        for rule_file in priority_rules:
            full_path = os.path.join(rules_path, rule_file)
            if os.path.exists(full_path):
                yara_files.append(full_path)
        
        # Then, add rules from priority categories
        for category in priority_categories:
            category_path = os.path.join(rules_path, category)
            if os.path.exists(category_path):
                for root, dirs, files in os.walk(category_path):
                    for file in files:
                        if file.endswith(('.yar', '.yara')):
                            rule_path = os.path.join(root, file)
                            if rule_path not in yara_files:
                                yara_files.append(rule_path)
                                # Limit total rules to prevent timeout
                                if len(yara_files) >= 15:
                                    break
                    if len(yara_files) >= 15:
                        break
            if len(yara_files) >= 15:
                break
        
        if not yara_files:
            print(f"[YARA] No YARA rules found", file=sys.stderr, flush=True)
            return matches
        
        print(f"[YARA] Scanning with {len(yara_files)} rule files (media-focused)", file=sys.stderr, flush=True)
        
        # Scan with priority rules (YARA accepts multiple rule files)
        try:
            result = subprocess.run(
                ["yara", "-s"] + yara_files + [file_path],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout for YARA scan
            )
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        # YARA output format: rule_name file_path
                        parts = line.split()
                        if parts:
                            rule_name = parts[0]
                            if rule_name and rule_name not in matches:
                                matches.append(rule_name)
            
            print(f"[YARA] Scan completed. Matches: {len(matches)}", file=sys.stderr, flush=True)
        except subprocess.TimeoutExpired:
            print(f"[YARA] Timeout scanning: {file_path}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[YARA] Error: {str(e)}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[YARA] Fatal error: {str(e)}", file=sys.stderr, flush=True)
    
    return matches


def scan_file(file_path: str) -> dict:
    """Scan a single file."""
    if not os.path.exists(file_path):
        return {
            "error": f"File not found: {file_path}", 
            "is_infected": False,
            "scanned_files": [],
            "infected_files": []
        }
    
    # First scan with ClamAV (faster, more reliable)
    is_infected, virus_name = scan_with_clamav(file_path)
    
    # Then scan with YARA (can be slow with many rules, so we limit it)
    # If YARA times out, we still return ClamAV results
    yara_matches = []
    try:
        yara_matches = scan_with_yara(file_path)
        if yara_matches:
            is_infected = True
    except Exception as e:
        print(f"[YARA] YARA scan failed, continuing with ClamAV results: {str(e)}", file=sys.stderr, flush=True)
    
    # Build response with file lists (for consistency with directory scanning)
    scanned_files = [file_path]
    infected_files = [file_path] if is_infected else []
    
    return {
        "is_infected": is_infected,
        "virus_name": virus_name,
        "yara_matches": yara_matches,
        "file_path": file_path,
        "scanned_files": scanned_files,
        "infected_files": infected_files
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
            print(f"[HTTP] GET /health - Health check request", file=sys.stderr, flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            print(f"[HTTP] GET {self.path} - 404 Not Found", file=sys.stderr, flush=True)
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests - scan files."""
        print(f"[HTTP] POST {self.path} - Request received", file=sys.stderr, flush=True)
        
        if self.path != "/scan":
            print(f"[HTTP] POST {self.path} - 404 Not Found (expected /scan)", file=sys.stderr, flush=True)
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            path = data.get("path")
            
            print(f"[SCAN] Received scan request for path: {path}", file=sys.stderr, flush=True)
            
            if not path:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No path provided"}).encode())
                return
            
            # Check if path exists
            if not os.path.exists(path):
                print(f"[SCAN] Path does not exist: {path}", file=sys.stderr, flush=True)
                result = {
                    "error": f"Path not found: {path}", 
                    "is_infected": False,
                    "scanned_files": [],
                    "infected_files": []
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            
            # Determine if file or directory
            print(f"[SCAN] Starting scan...", file=sys.stderr, flush=True)
            if os.path.isfile(path):
                result = scan_file(path)
            elif os.path.isdir(path):
                result = scan_directory(path)
            else:
                result = {"error": f"Path not found: {path}"}
            
            print(f"[SCAN] Scan completed. Infected: {result.get('is_infected', False)}", file=sys.stderr, flush=True)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print(f"[SCAN] Error during scan: {str(e)}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc(file=sys.stderr)
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
    print(f"[HTTP] Scan service listening on port {PORT}", file=sys.stderr, flush=True)
    print(f"[HTTP] Ready to accept scan requests", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"[HTTP] Shutting down scan service", file=sys.stderr, flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()

