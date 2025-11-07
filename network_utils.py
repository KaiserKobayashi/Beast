"""
network_utils.py

Network utilities for checking connectivity and handling firewall issues
when using edge-tts for voice synthesis.
"""

import asyncio
import socket
from typing import Tuple, Optional


def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
    """
    Check if internet connection is available.
    
    Args:
        host: Host to connect to (default: Google DNS)
        port: Port to connect to
        timeout: Connection timeout in seconds
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, socket.timeout):
        return False


async def check_edge_tts_api(timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if edge-tts API is accessible.
    
    Args:
        timeout: Connection timeout in seconds
    
    Returns:
        Tuple of (is_accessible, error_message)
    """
    try:
        import edge_tts
        
        # Try to list voices as a connection test
        try:
            voices = await asyncio.wait_for(
                edge_tts.list_voices(),
                timeout=timeout
            )
            if voices:
                return True, None
            else:
                return False, "No voices returned from API"
        except asyncio.TimeoutError:
            return False, "Connection timeout - API may be blocked by firewall"
        except Exception as e:
            error_msg = str(e)
            if "DNS" in error_msg or "No address" in error_msg:
                return False, "DNS resolution failed - check network/firewall settings"
            elif "Connection" in error_msg or "refused" in error_msg:
                return False, "Connection refused - API may be blocked by firewall"
            else:
                return False, f"API error: {error_msg}"
    except ImportError:
        return False, "edge-tts not installed"


def test_edge_tts_connection() -> dict:
    """
    Test edge-tts connectivity and return detailed results.
    
    Returns:
        Dictionary with test results
    """
    results = {
        "internet_connected": False,
        "edge_tts_accessible": False,
        "error_message": None,
        "recommendations": []
    }
    
    # Test basic internet connectivity
    results["internet_connected"] = check_internet_connection()
    
    if not results["internet_connected"]:
        results["error_message"] = "No internet connection detected"
        results["recommendations"].extend([
            "Check your network connection",
            "Verify you're not in offline mode",
            "Check if other internet services work"
        ])
        return results
    
    # Test edge-tts API accessibility
    try:
        accessible, error = asyncio.run(check_edge_tts_api())
        results["edge_tts_accessible"] = accessible
        
        if not accessible:
            results["error_message"] = error
            
            if "firewall" in error.lower() or "blocked" in error.lower():
                results["recommendations"].extend([
                    "Edge-TTS API (api.msedgeservices.com) may be blocked by firewall",
                    "Contact your network administrator to allow access to:",
                    "  - api.msedgeservices.com (HTTPS/443)",
                    "  - *.speech.microsoft.com (HTTPS/443)",
                    "Alternative: Use a different TTS engine or work offline with pre-generated audio"
                ])
            elif "DNS" in error:
                results["recommendations"].extend([
                    "DNS resolution failed for Microsoft edge-tts services",
                    "Try using a different DNS server (e.g., 8.8.8.8)",
                    "Check if your network blocks Microsoft Azure services"
                ])
            else:
                results["recommendations"].append(f"API error: {error}")
    except Exception as e:
        results["error_message"] = f"Unexpected error: {str(e)}"
        results["recommendations"].append("Contact support with this error message")
    
    return results


def get_firewall_help_text() -> str:
    """
    Get help text for firewall configuration.
    
    Returns:
        Formatted help text
    """
    return """
╔══════════════════════════════════════════════════════════════════════╗
║                    FIREWALL CONFIGURATION HELP                       ║
╚══════════════════════════════════════════════════════════════════════╝

The Beast TTS application uses Microsoft Azure Edge TTS service, which
requires network access to function properly.

REQUIRED NETWORK ACCESS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• api.msedgeservices.com (Port 443/HTTPS)
• *.speech.microsoft.com (Port 443/HTTPS)

COMMON FIREWALL ISSUES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Corporate Firewalls
   → Contact your IT department to whitelist the domains above
   
2. Proxy Servers
   → Configure system proxy settings or use environment variables:
     export HTTPS_PROXY=http://proxy.example.com:8080
   
3. VPN Restrictions
   → Try disconnecting from VPN or configure split tunneling
   
4. Antivirus/Security Software
   → Add Beast application to trusted applications list

TESTING CONNECTIVITY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run this command to test your connection:
    python -c "from network_utils import test_edge_tts_connection; 
               import json; print(json.dumps(test_edge_tts_connection(), indent=2))"

ALTERNATIVE SOLUTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you cannot modify firewall rules, consider:
• Use pre-generated audio files (offline mode)
• Install a local TTS engine (pyttsx3, gTTS with offline mode)
• Work with IT to set up a proxy exception
• Use the application on a different network

For more help, see: FIREWALL_TROUBLESHOOTING.md
"""


if __name__ == "__main__":
    # Run connectivity test when module is executed directly
    import json
    print("Testing edge-tts connectivity...\n")
    results = test_edge_tts_connection()
    
    print(json.dumps(results, indent=2))
    print()
    
    if not results["edge_tts_accessible"]:
        print("⚠️  CONNECTION ISSUES DETECTED")
        print()
        if results["recommendations"]:
            print("Recommendations:")
            for rec in results["recommendations"]:
                print(f"  • {rec}")
        print()
        print("For detailed help, run:")
        print("  python -c \"from network_utils import get_firewall_help_text; print(get_firewall_help_text())\"")
    else:
        print("✅ Connection successful! Edge-TTS is accessible.")
