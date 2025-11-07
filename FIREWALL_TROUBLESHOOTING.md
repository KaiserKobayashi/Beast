# Firewall Troubleshooting Guide

## Overview

Beast TTS uses Microsoft Azure Edge TTS service, which requires internet connectivity. If you're experiencing connection issues, this guide will help you diagnose and resolve firewall-related problems.

## Quick Diagnosis

Run the built-in connectivity test:

```bash
python network_utils.py
```

This will check:
- ✓ Internet connectivity
- ✓ Edge-TTS API accessibility
- ✓ Specific error conditions
- ✓ Recommended solutions

## Required Network Access

For Beast TTS to function, the following domains must be accessible:

| Domain | Port | Protocol | Purpose |
|--------|------|----------|---------|
| `api.msedgeservices.com` | 443 | HTTPS | Edge-TTS API endpoint |
| `*.speech.microsoft.com` | 443 | HTTPS | Azure Speech Services |

## Common Firewall Scenarios

### 1. Corporate/Enterprise Firewall

**Symptoms:**
- Connection timeout errors
- DNS resolution failures
- "API may be blocked by firewall" messages

**Solutions:**

a) **Request Firewall Exception:**
   - Contact your IT department
   - Request access to: `api.msedgeservices.com` and `*.speech.microsoft.com`
   - Provide this documentation to your IT team

b) **Use Proxy Authentication:**
   ```bash
   # Set environment variables (Linux/Mac)
   export HTTPS_PROXY=http://username:password@proxy.company.com:8080
   export HTTP_PROXY=http://username:password@proxy.company.com:8080
   
   # Windows Command Prompt
   set HTTPS_PROXY=http://username:password@proxy.company.com:8080
   set HTTP_PROXY=http://username:password@proxy.company.com:8080
   
   # Windows PowerShell
   $env:HTTPS_PROXY="http://username:password@proxy.company.com:8080"
   $env:HTTP_PROXY="http://username:password@proxy.company.com:8080"
   ```

### 2. VPN Restrictions

**Symptoms:**
- Works without VPN, fails with VPN connected
- Intermittent connectivity

**Solutions:**

a) **Split Tunneling:**
   - Configure VPN to exclude Microsoft Azure domains
   - Add exception routes for speech services

b) **Temporary Disconnect:**
   - Process TTS content while disconnected from VPN
   - Reconnect after generation complete

### 3. Antivirus/Security Software

**Symptoms:**
- SSL certificate errors
- Connection blocked messages
- Python process blocked

**Solutions:**

a) **Whitelist Application:**
   - Add `python.exe` or `pythonw.exe` to trusted applications
   - Allow network access for Beast application directory

b) **Disable SSL Inspection:**
   - Temporarily disable SSL/TLS inspection for Microsoft domains
   - Add exception for Azure services

### 4. ISP or Regional Blocks

**Symptoms:**
- Service works on mobile network but not home/work network
- Geographic restrictions

**Solutions:**

a) **Check Service Availability:**
   - Verify Azure Speech Services are available in your region
   - Try different network (mobile hotspot, different ISP)

b) **Use VPN (Reverse):**
   - Connect to VPN in region where service is available
   - Route through different geographic location

## Testing Connectivity Step-by-Step

### Step 1: Basic Internet Test

```bash
# Test basic internet (ping Google DNS)
ping 8.8.8.8
```

Expected: Should receive replies

### Step 2: DNS Resolution Test

```bash
# Test DNS resolution for Azure services
nslookup api.msedgeservices.com
```

Expected: Should return IP addresses

### Step 3: HTTPS Connectivity Test

```bash
# Linux/Mac
curl -I https://api.msedgeservices.com

# Windows PowerShell
Invoke-WebRequest -Uri https://api.msedgeservices.com -Method Head
```

Expected: Should connect (may return 404, but connection succeeds)

### Step 4: Edge-TTS Test

```bash
# Run Beast's built-in test
python network_utils.py
```

Expected output:
```json
{
  "internet_connected": true,
  "edge_tts_accessible": true,
  "error_message": null,
  "recommendations": []
}
```

## Error Messages and Solutions

### Error: "Connection timeout - API may be blocked by firewall"

**Cause:** Firewall is blocking outbound HTTPS to Microsoft Azure

**Fix:**
1. Contact network administrator
2. Request whitelist for domains listed above
3. Provide IT with this document

### Error: "DNS resolution failed - check network/firewall settings"

**Cause:** DNS server cannot resolve Microsoft Azure domains

**Fix:**
1. Try alternative DNS:
   ```bash
   # Use Google DNS
   # Windows: Network settings → Change adapter → IPv4 → DNS: 8.8.8.8, 8.8.4.4
   # Linux: Edit /etc/resolv.conf → nameserver 8.8.8.8
   ```
2. Check if DNS filtering is blocking Microsoft domains

### Error: "Connection refused - API may be blocked by firewall"

**Cause:** Firewall actively rejecting connections

**Fix:**
1. Check local firewall settings
2. Check corporate firewall rules
3. Verify proxy configuration

### Error: "No internet connection detected"

**Cause:** No network connectivity

**Fix:**
1. Check physical network connection
2. Verify WiFi/Ethernet is connected
3. Test with other applications

## Offline Alternatives

If firewall modifications are not possible, consider these alternatives:

### 1. Pre-Generate Audio Files

Process content on a network where TTS works, then transfer files:

```bash
# On accessible network
python beast_gui.py  # Generate all TTS files

# Transfer the output folder to restricted network
# Use pre-generated audio without regenerating
```

### 2. Use Local TTS Engine

Modify `tts_helpers.py` to use offline TTS engines:

```python
# Install offline TTS
pip install pyttsx3  # Windows: SAPI, Mac: NSSpeechSynthesizer, Linux: espeak

# Use offline engine (requires code modification)
# See: Alternative TTS Engines section
```

### 3. Batch Processing

- Generate TTS on personal device/network
- Transfer to restricted environment
- Process video/subtitle operations offline

## IT Department Request Template

If you need to request firewall access from your IT department, use this template:

---

**Subject:** Firewall Exception Request for Microsoft Azure Speech Services

**Application:** Beast TTS (Text-to-Speech application)

**Business Justification:** 
[Describe your use case for TTS - e.g., accessibility, content creation, language learning]

**Required Access:**

1. **Domain:** api.msedgeservices.com
   - **Port:** 443 (HTTPS)
   - **Direction:** Outbound
   - **Purpose:** Microsoft Edge TTS API endpoint

2. **Domain:** *.speech.microsoft.com  
   - **Port:** 443 (HTTPS)
   - **Direction:** Outbound
   - **Purpose:** Azure Speech Services

**Security Notes:**
- HTTPS encrypted traffic only
- Microsoft Azure trusted service
- No inbound ports required
- Read-only API access (no data upload)

**Impact if Denied:**
[Describe impact - e.g., cannot generate speech audio, workflow blocked]

**Alternative Solutions Considered:**
- Local TTS engines (inferior quality)
- Manual voice recording (time-consuming)
- Pre-generation on external network (inconvenient)

---

## Advanced Troubleshooting

### Enable Debug Logging

Add debug output to see connection details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test with curl

Manual API test:

```bash
curl -v https://api.msedgeservices.com/api/tts/v1/voices
```

### Check Proxy Settings

```bash
# Linux/Mac
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Windows
echo %HTTP_PROXY%
echo %HTTPS_PROXY%
```

### Network Trace

For IT department troubleshooting:

```bash
# Windows
netsh trace start capture=yes tracefile=beast_tts.etl

# Linux
sudo tcpdump -i any -w beast_tts.pcap host api.msedgeservices.com
```

## Contact Support

If you've tried all solutions and still have issues:

1. Run full diagnostic:
   ```bash
   python network_utils.py > diagnostic_output.txt
   ```

2. Include in support request:
   - Diagnostic output
   - Network environment (corporate/home/VPN)
   - Firewall/proxy configuration
   - Error messages from application

## See Also

- [QUICKSTART.md](QUICKSTART.md) - Basic setup guide
- [VOICE_CONFIG_GUIDE.md](VOICE_CONFIG_GUIDE.md) - Voice configuration
- [README.md](README.md) - General documentation
