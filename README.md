# Multi-Threaded Server Project

A comprehensive networking project implementing various types of servers and clients with multi-threading capabilities, packet crafting, and network utilities for both TCP and UDP protocols.

## 🚀 Features

### TCP Implementations
- **Multi-threaded TCP Server** (`tcp_multi_threaded_server.py`) - Handles multiple concurrent client connections using threading
- **Simple TCP Server** (`tcp_simple_server.py`) - Basic TCP server with automatic port binding
- **TCP Clients** - Both simple and multi-threaded client implementations
- **TCP Packet Crafting** (`tcp_packet_crafter.py`) - Raw TCP packet creation with checksum calculation

### UDP Implementations
- **UDP Server Class** (`udp_server_class.py`) - Object-oriented UDP server with logging and time synchronization
- **UDP Server Main** (`udp_server_main.py`) - Main UDP server application with time difference calculations
- **UDP Clients** - Simple and fast UDP client implementations
- **UDP Packet Crafting** (`udp_packet_crafter_class.py`) - UDP packet creation utilities
- **Adaptive UDP Time-Sync Lab** (`udp_server_main.py` + `udp_simple_client.py`)
  - Computes three correction schemes per packet: RAW, EWMA, Kalman
  - Uses `IDCODE` field so each client receives **only** its chosen scheme
  - Live plots (matplotlib) with colored curves & per-scheme histograms
  - JSON-based feedback (`{"scheme":"ewma","correction_us":…}`)
- **PID Forecast Scheme** – Adds classical PID controller smoothing; choose with `--mode pid`.

### Utility Features
- **Debugging & Logging** (`util.py`) - Comprehensive logging system with file output
- **Time Synchronization** - NTP-based time sync utilities
- **Firewall Configuration** (`util_firewall.sh`) - iptables rules for network security
- **Network Utilities** - IP configuration and network setup scripts

## 📁 Project Structure

```
├── TCP Servers & Clients
│   ├── tcp_multi_threaded_server.py    # Multi-threaded TCP server
│   ├── tcp_simple_server.py            # Basic TCP server
│   ├── tcp_multi_thread_client.py      # Multi-threaded TCP client
│   ├── tcp_simple_client.py            # Simple TCP client
│   └── tcp_packet_crafter.py           # Raw TCP packet crafting
│
├── UDP Servers & Clients
│   ├── udp_server_class.py             # UDP server class implementation
│   ├── udp_server_main.py              # Main UDP server application
│   ├── udp_simple_server.py            # Simple UDP server
│   ├── udp_simple_client.py            # Basic UDP client
│   ├── udp_simple_client_fast.py       # Optimized UDP client
│   ├── udp_packet_crafter_class.py     # UDP packet crafting utilities
│   └── udp_payloads.py                 # UDP payload handling
│
├── Utilities & Configuration
│   ├── util.py                         # Debugging and utility functions
│   ├── util_firewall.sh                # Firewall configuration script
│   ├── util_firewall_default_policy.sh # Default firewall policies
│   ├── util_setting_ip.sh              # IP configuration script
│   └── util_time_sync_manual.txt       # Time synchronization guide
│
└── Documentation & Examples
    ├── README.md                        # This file
    ├── mozilla_bookmarks.txt            # Reference bookmarks
    └── *.zip files                      # Example code archives
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.x
- Linux environment (WSL2 supported)
- Required Python packages:
  ```bash
  pip install pytz
  ```

### Network Configuration
1. The project is configured for localhost testing:
   - Default server IP: `127.0.0.1` (localhost)
   - Default port: `12345`
   - For network deployment, update IP addresses in server files as needed

2. Configure firewall rules (optional):
   ```bash
   chmod +x util_firewall.sh
   sudo ./util_firewall.sh
   ```

## 🚀 Usage

### TCP Multi-threaded Server
```bash
# Start the multi-threaded TCP server
python3 tcp_multi_threaded_server.py

# Connect with a client
python3 tcp_multi_thread_client.py
```

### UDP Server with Time Synchronization
```bash
# Start the UDP server with logging
python3 udp_server_main.py

# Send packets from UDP client
python3 udp_simple_client.py
```

### Simple Servers (for testing)
```bash
# Basic TCP server
python3 tcp_simple_server.py

# Basic UDP server
python3 udp_simple_server.py
```

## 🔧 Key Components

### Multi-threading Support
- TCP server uses `_thread.start_new_thread()` for handling concurrent connections
- Each client connection runs in a separate thread
- Thread counting and management included

### Logging & Debugging
- Comprehensive logging system with file output to `logs/` directory
- Timestamp-based logging with function-level tracking
- Verbose mode support for detailed debugging
- Custom debugger class with log rotation

### Time Synchronization
- NTP-based time synchronization utilities
- Microsecond-precision time difference calculations
- Server-client time offset calculations
- Automatic time sync daemon support

### Packet Crafting
- Raw TCP packet creation with proper checksum calculation
- UDP packet crafting with custom headers
- Protocol-specific frame building utilities
- Binary data structure packing/unpacking

### Network Security
- iptables-based firewall configuration
- Port range restrictions
- IP-based access control
- SSH and service-specific rules

## 📋 Configuration

### Server Configuration
Edit the following variables in server files:
```python
IP_SERVER_IS_BINDING = '127.0.0.1'    # Server bind IP (localhost)
PORT_OPENING = 12345                   # Server port
BUFFER_SIZE = 1024                     # Buffer size for data transfer
```

### Client Configuration
Update client connection settings:
```python
SERVER_IP = '127.0.0.1'               # Target server IP (localhost)
SERVER_PORT = 12345                    # Target server port
# Select scheme at runtime
python3 udp_simple_client.py --mode raw|ewma|kalman [--count N]
```

## 🧪 Testing

### Test Multi-threading
1. Start the multi-threaded TCP server
2. Connect multiple clients simultaneously
3. Verify thread creation and independent message handling

### Test Time Synchronization
1. Start UDP server with time sync enabled
2. Send timestamped packets from clients
3. Check time difference calculations in server logs

### Test Packet Crafting
1. Use the packet crafter utilities to create custom packets
2. Verify packet structure with network analysis tools
3. Test checksum calculations

## 🔍 Monitoring & Logs

- Server logs are stored in `logs/` directory
- Each component creates separate log files
- Timestamps and function-level logging available
- Network traffic can be monitored using firewall rules

## 🤝 Contributing

This project serves as a comprehensive networking laboratory for:
- Learning multi-threaded server programming
- Understanding TCP/UDP protocol implementations
- Testing network security configurations
- Experimenting with packet-level networking

## 📄 License

This project is designed for educational and testing purposes.

---

**Researcher:** Rishabh Dubey  
**Environment:** Linux/WSL2 compatible  
**Python Version:** 3.x required

## 📊 Live Plotting
When the server starts choose plot option **1** (live window) or **2** (periodic PNGs).

Color key  RAW = blue  EWMA = green  Kalman = orange.  Histograms are over-laid per scheme so you can see which distribution is tightest around **0 ms**.

## 🏃 Quick Demo (3 clients in parallel)

```bash
# terminal-1 : start server with plotting
make udp-server        # choose option 1

# terminal-2 : fire three clients (RAW / EWMA / Kalman)
make three-clients     # background processes
```

Each client automatically sends its scheme `IDCODE` (0x0001/2/3). The server replies with the matching correction only.

## 🆕 Makefile shortcuts
- `make three-clients`  Start EWMA, Kalman, PID clients (50 pkts each).
- `make four-clients`  Start RAW, EWMA, Kalman, PID clients.
- `make udp-server`        Start server with RAW shown.
- `make udp-server -- --hide-raw` or run script manually to hide RAW.

---
