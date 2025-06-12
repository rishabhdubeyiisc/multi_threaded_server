# Multi-Threaded Server Project Makefile
# Author: Rishabh Dubey

# Configuration
PYTHON := python3
SERVER_IP := 127.0.0.1
SERVER_PORT := 12345

# Default target
.PHONY: help
help:
	@echo "Multi-Threaded Server Project - Available Commands:"
	@echo ""
	@echo "🚀 Server Commands:"
	@echo "  make tcp-server          - Start TCP multi-threaded server"
	@echo "  make tcp-server-simple   - Start simple TCP server"
	@echo "  make udp-server          - Start UDP server with logging"
	@echo "  make udp-server-simple   - Start simple UDP server"
	@echo ""
	@echo "📱 Client Commands:"
	@echo "  make tcp-client          - Start TCP multi-threaded client"
	@echo "  make tcp-client-simple   - Start simple TCP client"
	@echo "  make udp-client          - Start UDP client"
	@echo "  make udp-client-fast     - Start fast UDP client"
	@echo ""
	@echo "🛠️  Setup & Utilities:"
	@echo "  make install             - Install Python dependencies"
	@echo "  make firewall-setup      - Configure firewall rules (requires sudo)"
	@echo "  make firewall-default    - Set default firewall policies (requires sudo)"
	@echo "  make clean               - Clean up log files and temporary data"
	@echo "  make logs                - View recent server logs"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test-tcp            - Test TCP server with multiple clients"
	@echo "  make test-udp            - Test UDP server with time sync"
	@echo "  make demo                - Run interactive demo"
	@echo ""
	@echo "📋 Info Commands:"
	@echo "  make status              - Show running servers and network status"
	@echo "  make config              - Show current configuration"

# Installation and Setup
.PHONY: install
install:
	@echo "Installing Python dependencies..."
	pip3 install pytz
	@echo "Dependencies installed successfully!"

.PHONY: firewall-setup
firewall-setup:
	@echo "Setting up firewall rules..."
	chmod +x util_firewall.sh
	sudo ./util_firewall.sh
	@echo "Firewall rules configured!"

.PHONY: firewall-default
firewall-default:
	@echo "Setting default firewall policies..."
	chmod +x util_firewall_default_policy.sh
	sudo ./util_firewall_default_policy.sh
	@echo "Default firewall policies set!"

# TCP Server Commands
.PHONY: tcp-server
tcp-server:
	@echo "Starting TCP Multi-threaded Server on $(SERVER_IP):$(SERVER_PORT)..."
	@echo "Press Ctrl+C to stop the server"
	$(PYTHON) tcp_multi_threaded_server.py

.PHONY: tcp-server-simple
tcp-server-simple:
	@echo "Starting Simple TCP Server on $(SERVER_IP):$(SERVER_PORT)..."
	@echo "Press Ctrl+C to stop the server"
	$(PYTHON) tcp_simple_server.py

# UDP Server Commands
.PHONY: udp-server
udp-server:
	@echo "Starting UDP Server with logging on $(SERVER_IP):$(SERVER_PORT)..."
	@echo "Press Ctrl+C to stop the server"
	$(PYTHON) udp_server_main.py

.PHONY: udp-server-simple
udp-server-simple:
	@echo "Starting Simple UDP Server on $(SERVER_IP):$(SERVER_PORT)..."
	@echo "Press Ctrl+C to stop the server"
	$(PYTHON) udp_simple_server.py

.PHONY: udp-server-noraw
udp-server-noraw:
	$(PYTHON) udp_server_main.py --hide-raw

# Client Commands
.PHONY: tcp-client
tcp-client:
	@echo "Starting TCP Multi-threaded Client..."
	@echo "Connecting to $(SERVER_IP):$(SERVER_PORT)"
	$(PYTHON) tcp_multi_thread_client.py

.PHONY: tcp-client-simple
tcp-client-simple:
	@echo "Starting Simple TCP Client..."
	@echo "Connecting to $(SERVER_IP):$(SERVER_PORT)"
	$(PYTHON) tcp_simple_client.py

.PHONY: udp-client
udp-client:
	@echo "Starting UDP Client..."
	@echo "Connecting to $(SERVER_IP):$(SERVER_PORT)"
	$(PYTHON) udp_simple_client.py

.PHONY: udp-client-fast
udp-client-fast:
	@echo "Starting Fast UDP Client..."
	@echo "Connecting to $(SERVER_IP):$(SERVER_PORT)"
	$(PYTHON) udp_simple_client_fast.py

# Testing Commands
.PHONY: test-tcp
test-tcp:
	@echo "Testing TCP Multi-threaded Server..."
	@echo "This will start the server in background and test with multiple clients"
	@echo "Starting TCP server in background..."
	$(PYTHON) tcp_multi_threaded_server.py &
	@sleep 2
	@echo "Testing with multiple clients..."
	@echo "Client 1:" && echo "test message 1" | $(PYTHON) tcp_multi_thread_client.py &
	@echo "Client 2:" && echo "test message 2" | $(PYTHON) tcp_multi_thread_client.py &
	@echo "Client 3:" && echo "test message 3" | $(PYTHON) tcp_multi_thread_client.py &
	@sleep 5
	@pkill -f tcp_multi_threaded_server.py || true
	@echo "TCP test completed!"

.PHONY: test-udp
test-udp:
	@echo "Testing UDP Server with time synchronization..."
	@echo "Starting UDP server in background..."
	$(PYTHON) udp_server_main.py &
	@sleep 2
	@echo "Sending test packets..."
	@timeout 10 $(PYTHON) udp_simple_client.py || true
	@pkill -f udp_server_main.py || true
	@echo "UDP test completed!"

.PHONY: demo
demo:
	@echo "🎯 Multi-Threaded Server Demo"
	@echo "Choose a demo option:"
	@echo "1. TCP Multi-threaded Server Demo"
	@echo "2. UDP Server with Time Sync Demo"
	@echo "3. Packet Crafting Demo"
	@read -p "Enter choice (1-3): " choice; \
	case $$choice in \
		1) echo "Starting TCP Demo..." && $(MAKE) tcp-server ;; \
		2) echo "Starting UDP Demo..." && $(MAKE) udp-server ;; \
		3) echo "Running Packet Crafting Demo..." && $(PYTHON) tcp_packet_crafter.py ;; \
		*) echo "Invalid choice!" ;; \
	esac

# Utility Commands
.PHONY: clean
clean:
	@echo "Cleaning up logs and temporary files..."
	rm -rf logs/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf *.png
	find . -name "*.log" -delete
	@echo "Cleanup completed!"

.PHONY: logs
logs:
	@echo "Recent server logs:"
	@if [ -d "logs" ]; then \
		echo "=== UDP Server Logs ==="; \
		tail -n 20 logs/UDP_server.log 2>/dev/null || echo "No UDP server logs found"; \
		echo ""; \
		echo "=== Other Log Files ==="; \
		ls -la logs/ 2>/dev/null || echo "No log directory found"; \
	else \
		echo "No logs directory found. Run a server first to generate logs."; \
	fi

.PHONY: status
status:
	@echo "📊 Server Status:"
	@echo "Running Python processes:"
	@ps aux | grep python | grep -E "(tcp_|udp_)" | grep -v grep || echo "No servers currently running"
	@echo ""
	@echo "Network connections on port $(SERVER_PORT):"
	@netstat -tulpn 2>/dev/null | grep $(SERVER_PORT) || echo "No connections on port $(SERVER_PORT)"
	@echo ""
	@echo "Active firewall rules:"
	@sudo iptables -L INPUT 2>/dev/null | head -10 || echo "Cannot check firewall rules (requires sudo)"

.PHONY: config
config:
	@echo "📋 Current Configuration:"
	@echo "Python Version: $(shell $(PYTHON) --version)"
	@echo "Server IP: $(SERVER_IP)"
	@echo "Server Port: $(SERVER_PORT)"
	@echo "Project Directory: $(PWD)"
	@echo ""
	@echo "Available Python files:"
	@ls -la *.py
	@echo ""
	@echo "Available shell scripts:"
	@ls -la *.sh 2>/dev/null || echo "No shell scripts found"

# Background server management
.PHONY: start-tcp-bg
start-tcp-bg:
	@echo "Starting TCP server in background..."
	nohup $(PYTHON) tcp_multi_threaded_server.py > tcp_server.log 2>&1 &
	@echo "TCP server started in background (PID: $$!)"

.PHONY: start-udp-bg
start-udp-bg:
	@echo "Starting UDP server in background..."
	nohup $(PYTHON) udp_server_main.py > udp_server.log 2>&1 &
	@echo "UDP server started in background (PID: $$!)"

.PHONY: stop-servers
stop-servers:
	@echo "Stopping all running servers..."
	@pkill -f tcp_multi_threaded_server.py || true
	@pkill -f tcp_simple_server.py || true
	@pkill -f udp_server_main.py || true
	@pkill -f udp_simple_server.py || true
	@echo "All servers stopped!"

# Development helpers
.PHONY: dev-setup
dev-setup: install clean
	@echo "Setting up development environment..."
	@echo "Creating logs directory..."
	@mkdir -p logs
	@echo "Development environment ready!"

.PHONY: quick-test
quick-test:
	@echo "Quick functionality test..."
	@echo "Testing Python syntax..."
	@$(PYTHON) -m py_compile tcp_multi_threaded_server.py
	@$(PYTHON) -m py_compile udp_server_main.py
	@echo "All Python files compile successfully!"

# New target
.PHONY: three-clients four-clients
three-clients: 
	@echo "Starting three UDP clients (EWMA, Kalman, PID) in background..."
	$(PYTHON) udp_simple_client.py --mode ewma --count 50 &
	$(PYTHON) udp_simple_client.py --mode kalman --count 50 &
	$(PYTHON) udp_simple_client.py --mode pid --count 50 &
	sleep 1
	@echo "Clients started (PIDs above). Use 'ps aux | grep udp_simple_client.py' to view."

four-clients:
	@echo "Starting four UDP clients (RAW, EWMA, Kalman, PID) in background..."
	$(PYTHON) udp_simple_client.py --mode raw --count 50 &
	$(PYTHON) udp_simple_client.py --mode ewma --count 50 &
	$(PYTHON) udp_simple_client.py --mode kalman --count 50 &
	$(PYTHON) udp_simple_client.py --mode pid --count 50 &
	sleep 1
	@echo "Clients started (PIDs above). Use 'ps aux | grep udp_simple_client.py' to view."

# Default target when no arguments provided
.DEFAULT_GOAL := help 