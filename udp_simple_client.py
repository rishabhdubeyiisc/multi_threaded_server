#! /usr/bin/env python3
import socket
import datetime
import pytz
from time import time
import struct
import json
import argparse

from udp_packet_crafter_class import Common_frame

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

# Time synchronization variables
local_time_offset = 0.0  # Time correction offset in seconds
sync_count = 0
total_corrections = 0.0

parser = argparse.ArgumentParser(description="UDP time sync client")
parser.add_argument('--mode', choices=['raw','ewma','kalman','pid'], help='Correction mode to use')
parser.add_argument('--count', type=int, default=0, help='Number of packets to send before exiting (0=unlimited)')
args = parser.parse_args()

print("🕐 NTP-like UDP Time Sync Client Started!")
print("🎯 Connecting to server at", f"{SERVER_IP}:{SERVER_PORT}")

if args.mode:
    mode_choice = {'raw':'1','ewma':'2','kalman':'3','pid':'4'}[args.mode]
else:
    mode_choice = input("Choose correction mode:\n1. RAW offset\n2. EWMA forecast\n3. Kalman forecast\n4. PID controller\nChoice (1/2/3/4): ").strip()

if mode_choice == "2":
    CORRECTION_FIELD = "ewma_correction_us"
    print("📐 Using EWMA forecast corrections")
elif mode_choice == "3":
    CORRECTION_FIELD = "kalman_correction_us"
    print("📐 Using Kalman forecast corrections")
elif mode_choice == "4":
    CORRECTION_FIELD = "pid_correction_us"
    print("📐 Using PID corrections")
else:
    CORRECTION_FIELD = "raw_correction_us"
    print("📐 Using RAW offset corrections")

print("📡 Starting time synchronization...")
print("=" * 50)

time_stamp = datetime.datetime.now(pytz.utc)

#protocol specific values
DATA_FRAME_VALUE = int(0xAA01)
MAX_FRAME_SIZE = int(0xFFFF)
IDCODE_VALUE = int(0x0002)
SOC_VALUE = int(0x99)
client_sock = socket.socket( family = socket.AF_INET, type= socket.SOCK_DGRAM )

# counters
sync_count = 0
max_packets = args.count if args.mode is not None or True else 0

# idcode per scheme for server awareness
MODE_ID_LOOKUP = {'raw':0x0001,'ewma':0x0002,'kalman':0x0003,'pid':0x0004}
if args.mode:
    MODE_ID = MODE_ID_LOOKUP[args.mode]
else:
    MODE_ID = MODE_ID_LOOKUP['raw' if mode_choice=='1' else ('ewma' if mode_choice=='2' else ('kalman' if mode_choice=='3' else 'pid'))]

def get_corrected_time():
    """Get local time with applied corrections"""
    return time() + local_time_offset

def apply_time_correction(correction_microseconds, round_trip_time_ms):
    """Apply time correction with network latency compensation (NTP-style)"""
    global local_time_offset, sync_count, total_corrections
    
    # Compensate for network latency (assume symmetric delay)
    network_delay_compensation = (round_trip_time_ms * 1000) / 2  # Convert to microseconds, divide by 2
    
    # Apply network delay compensation to the correction
    compensated_correction = correction_microseconds + network_delay_compensation
    
    correction_seconds = compensated_correction / 1000000.0
    
    # Adaptive damping factor - more aggressive initially, then gentle
    if sync_count < 5:
        damping_factor = 0.5  # 50% correction for first few packets
    elif sync_count < 10:
        damping_factor = 0.3  # 30% correction for next few
    else:
        damping_factor = 0.1  # 10% correction for steady state
    
    correction_to_apply = correction_seconds * damping_factor
    
    local_time_offset += correction_to_apply
    sync_count += 1
    total_corrections += abs(correction_seconds)
    
    return correction_to_apply, compensated_correction, network_delay_compensation

try:
    while True:
        #take input
        #payload = input("insert new payload > ")
        
        # Use corrected time for packet creation
        current_time = get_corrected_time()
        
        crafted_payload = Common_frame( SYNC        = int(DATA_FRAME_VALUE) , 
                                        FRAME_SIZE  = int(MAX_FRAME_SIZE), 
                                        IDCODE      = MODE_ID , 
                                        SOC         = int(current_time) , 
                                        FRACSEC     = int( (((repr(( current_time % 1))).split("."))[1])[0:6] ) , 
                                        CHK         = int(0xDEAD) )
        
        payload = crafted_payload.build()
        
        # Record send time for round-trip calculation
        send_time = time()
        
        #send
        client_sock.sendto( payload ,( SERVER_IP , SERVER_PORT) )
        
        #receive
        data_recvd , server_addr = client_sock.recvfrom(BUFFER_SIZE)
        receive_time = time()
        
        try:
            # Try to parse JSON correction data
            correction_data = json.loads(data_recvd.decode('utf-8'))
            
            round_trip_time = (receive_time - send_time) * 1000  # Convert to milliseconds
            
            # unified correction from server
            raw_correction_us = correction_data.get('correction_us')
            if raw_correction_us is None:
                print("❌ Server response missing 'correction_us'")
                continue

            # Apply time correction with network compensation
            applied_correction, compensated_correction, network_compensation = apply_time_correction(
                raw_correction_us, round_trip_time)
            
            print(f"📦 Packet #{sync_count}")
            print(f"   🕐 Server correction: {raw_correction_us:.0f} μs (scheme={correction_data.get('scheme')})")
            print(f"   🌐 Network delay compensation: {network_compensation:.0f} μs")
            print(f"   🔧 Compensated correction: {compensated_correction:.0f} μs")
            print(f"   ⚡ Applied correction: {applied_correction*1000000:.0f} μs")
            print(f"   🔄 Round trip time: {round_trip_time:.2f} ms")
            print(f"   📊 Total offset: {local_time_offset*1000000:.0f} μs")
            
            # Show sync quality based on compensated correction
            if abs(compensated_correction) < 1000:  # Less than 1ms
                print("   🟢 EXCELLENT sync quality")
            elif abs(compensated_correction) < 10000:  # Less than 10ms
                print("   🟡 GOOD sync quality")
            else:
                print("   🔴 POOR sync quality - needs adjustment")
            
            # Show improvement trend
            if sync_count > 1:
                improvement = abs(raw_correction_us) < abs(total_corrections / sync_count * 1000000)
                trend_emoji = "📈" if improvement else "📉"
                print(f"   {trend_emoji} Sync trend: {'Improving' if improvement else 'Degrading'}")
            
            # Auto-reset if sync is getting worse after many attempts
            if sync_count > 15 and abs(compensated_correction) > 500000:  # 500ms threshold
                print("   🔄 SYNC RESET: Large errors detected, resetting synchronization...")
                local_time_offset = 0.0
                sync_count = 0
                total_corrections = 0.0
            
            print("-" * 50)
            
        except (json.JSONDecodeError, KeyError):
            # Fallback for non-JSON responses
            print(f"📨 Server response: {data_recvd.decode('utf-8')}")
        
        # Adaptive sync interval - faster when sync is poor, slower when good
        if sync_count > 0:
            avg_error = abs(total_corrections / sync_count * 1000000) if sync_count > 0 else 0
            if avg_error > 100000:  # > 100ms average error
                sync_interval = 1.0  # 1 second - fast sync
            elif avg_error > 10000:  # > 10ms average error
                sync_interval = 2.0  # 2 seconds - normal sync
            else:
                sync_interval = 5.0  # 5 seconds - slow sync for stable systems
        else:
            sync_interval = 1.0
        
        # Wait before next sync
        import time as time_module
        time_module.sleep(sync_interval)

        if max_packets and sync_count >= max_packets:
            print("Reached requested packet count. Exiting.")
            break

except KeyboardInterrupt:
    print(f"\n🏁 Time sync client stopped")
    print(f"📊 Final Statistics:")
    print(f"   Total syncs: {sync_count}")
    print(f"   Final offset: {local_time_offset*1000000:.0f} μs")
    print(f"   Avg correction: {(total_corrections/sync_count)*1000000 if sync_count > 0 else 0:.0f} μs")

client_sock.close()
print("🔄 Closing socket...")
