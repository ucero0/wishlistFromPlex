#!/usr/bin/env python3
"""
HTTP Scan Server for Antivirus + YARA Scanning
Simple HTTP API that accepts a path (file or directory) and scans with both antivirus engine and YARA.
"""
import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Tuple, Optional, List

# Configuration
YARA_RULES_PATH = "/yara-rules"
CUSTOM_YARA_RULES_PATH = "/scan-service/yara-rules-custom"
PORT = 3311  # HTTP scan service port (different from antivirus daemon port 3310)


def scan_with_antivirus(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Scan a file with antivirus engine using clamdscan.
    
    Returns:
        Tuple of (is_infected, virus_name)
    """
    try:
        result = subprocess.run(
            ["clamdscan", "--no-summary", file_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # clamdscan returns 1 if virus found, 0 if clean
        if result.returncode == 1:
            output = result.stdout.strip()
            if "FOUND" in output:
                # Parse: "file_path: VirusName FOUND"
                parts = output.split(":")
                if len(parts) > 1:
                    virus_part = parts[1].strip()
                    virus_name = virus_part.replace("FOUND", "").strip()
                    return True, virus_name
                return True, "Unknown"
        return False, None
    except subprocess.TimeoutExpired:
        print(f"[ANTIVIRUS] Timeout scanning: {file_path}", file=sys.stderr, flush=True)
        return False, None
    except Exception as e:
        print(f"[ANTIVIRUS] Error scanning {file_path}: {str(e)}", file=sys.stderr, flush=True)
        return False, None


def scan_with_yara(file_path: str) -> List[str]:
    """
    Scan a file with YARA rules.
    
    Returns:
        List of matching YARA rule names
    """
    matches = []
    
    try:
        # Check if yara command exists
        if subprocess.run(["which", "yara"], capture_output=True).returncode != 0:
            return matches
        
        # Collect YARA rule files - prefer index files for better performance and error handling
        yara_files = []
        
        # Add custom rules first (if they exist)
        if os.path.exists(CUSTOM_YARA_RULES_PATH):
            for root, dirs, files in os.walk(CUSTOM_YARA_RULES_PATH):
                for file in files:
                    if file.endswith(('.yar', '.yara')):
                        yara_files.append(os.path.join(root, file))
        
        # Collect individual rule files (index files have errors that prevent YARA from working)
        # We'll scan in batches to avoid loading all problematic rules at once
        if os.path.exists(YARA_RULES_PATH):
            for root, dirs, files in os.walk(YARA_RULES_PATH):
                for file in files:
                    if file.endswith(('.yar', '.yara')) and not file.endswith('_index.yar'):
                        rule_path = os.path.join(root, file)
                        if rule_path not in yara_files:
                            yara_files.append(rule_path)
        
        if not yara_files:
            return matches
        
        # Scan with YARA rules in batches to avoid errors from problematic rules
        # preventing all scanning. Some rules have syntax errors that cause YARA to fail
        # when loading all rules at once, so we scan in smaller batches.
        try:
            batch_size = 50
            for i in range(0, len(yara_files), batch_size):
                batch = yara_files[i:i + batch_size]
                batch_result = subprocess.run(
                    ["yara", "-s"] + batch + [file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                # Process results from this batch even if there were errors
                # YARA may return non-zero if some rules have errors, but still report matches
                if batch_result.stdout:
                    for line in batch_result.stdout.strip().split("\n"):
                        if line and not line.startswith("error:") and not line.startswith("warning:"):
                            parts = line.split()
                            if parts:
                                rule_name = parts[0]
                                if rule_name and rule_name not in matches and not rule_name.startswith("0x"):
                                    matches.append(rule_name)
            
            # Create a result object for compatibility with the rest of the code
            result = type('obj', (object,), {
                'returncode': 0 if matches else 1,
                'stdout': '\n'.join(matches) if matches else '',
                'stderr': ''
            })()
            
            # Process YARA output even if returncode is non-zero (some rules may have errors,
            # but matches should still be reported). YARA returns 0 on success, 1 if no matches,
            # but may return non-zero if some rules have syntax errors even when matches are found.
            if result.stdout:
                # Parse YARA output: "rule_name file_path" or "rule_name file_path offset:match"
                for line in result.stdout.strip().split("\n"):
                    if line and not line.startswith("error:") and not line.startswith("warning:"):
                        parts = line.split()
                        if parts:
                            rule_name = parts[0]
                            # Only add valid rule names (not file paths or offsets)
                            if rule_name and rule_name not in matches and not rule_name.startswith("0x"):
                                matches.append(rule_name)
            
            # Log warnings/errors but don't fail the scan
            if result.stderr:
                # Filter out common warnings that don't affect functionality
                error_lines = [line for line in result.stderr.split("\n") 
                              if line and "error:" in line and "unknown module" not in line.lower()]
                if error_lines:
                    print(f"[YARA] Warnings/errors (non-fatal): {len(error_lines)} issues", 
                          file=sys.stderr, flush=True)
        except subprocess.TimeoutExpired:
            print(f"[YARA] Timeout scanning: {file_path}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[YARA] Error scanning {file_path}: {str(e)}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[YARA] Fatal error: {str(e)}", file=sys.stderr, flush=True)
    
    return matches


def scan_file(file_path: str) -> dict:
    """
    Scan a single file with antivirus engine and YARA (optimized).
    
    Optimization: If antivirus engine detects infection, skip YARA scan for performance.
    Only scan with YARA if antivirus doesn't detect anything (to catch things antivirus might miss).
    
    Returns:
        Dictionary with scan results
    """
    if not os.path.exists(file_path):
        return {
            "error": f"File not found: {file_path}",
            "is_infected": False,
            "virus_name": None,
            "yara_matches": [],
            "scanned_files": [],
            "infected_files": []
        }
    
    # Scan with antivirus engine first (faster)
    is_infected, virus_name = scan_with_antivirus(file_path)
    yara_matches = []
    
    # Only scan with YARA if antivirus engine didn't detect anything
    # This optimizes performance: if antivirus already found something, skip YARA
    if not is_infected:
        yara_matches = scan_with_yara(file_path)
        # If YARA found something, mark as infected
        if yara_matches:
            is_infected = True
    
    return {
        "is_infected": is_infected,
        "virus_name": virus_name,
        "yara_matches": yara_matches,
        "scanned_files": [file_path],
        "infected_files": [file_path] if is_infected else []
    }


def scan_directory(directory_path: str) -> dict:
    """
    Scan all files in a directory with both antivirus engine and YARA.
    
    Returns:
        Dictionary with scan results for all files
    """
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return {
            "error": f"Directory not found: {directory_path}",
            "is_infected": False,
            "virus_name": None,
            "yara_matches": [],
            "scanned_files": [],
            "infected_files": []
        }
    
    scanned_files = []
    infected_files = []
    all_virus_names = []
    all_yara_matches = []
    
    # Walk through directory and scan each file
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            scanned_files.append(file_path)
            
            # Scan the file
            result = scan_file(file_path)
            
            if result.get("is_infected"):
                infected_files.append(file_path)
                if result.get("virus_name"):
                    all_virus_names.append(result["virus_name"])
                all_yara_matches.extend(result.get("yara_matches", []))
    
    return {
        "is_infected": len(infected_files) > 0,
        "virus_name": all_virus_names[0] if all_virus_names else None,
        "yara_matches": list(set(all_yara_matches)),  # Remove duplicates
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
            # Read request body
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
            
            # Check if path exists
            if not os.path.exists(path):
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
            
            # Scan file or directory
            if os.path.isfile(path):
                result = scan_file(path)
            elif os.path.isdir(path):
                result = scan_directory(path)
            else:
                result = {
                    "error": f"Path is neither file nor directory: {path}",
                    "is_infected": False,
                    "scanned_files": [],
                    "infected_files": []
                }
            
            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
        except Exception as e:
            print(f"[ERROR] Scan request failed: {str(e)}", file=sys.stderr, flush=True)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


def main():
    """Start the HTTP scan server."""
    server = HTTPServer(("0.0.0.0", PORT), ScanHandler)
    print(f"[HTTP] Scan service listening on port {PORT}", file=sys.stderr, flush=True)
    print(f"[HTTP] Ready to accept scan requests at http://0.0.0.0:{PORT}/scan", file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"[HTTP] Shutting down scan service", file=sys.stderr, flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()
