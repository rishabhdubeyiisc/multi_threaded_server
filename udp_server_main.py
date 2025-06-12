#!/usr/bin/env python3
import udp_server_class
import struct
import time
import statistics
from collections import deque
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import threading
import argparse

# parse cli for hide-raw
parser_srv = argparse.ArgumentParser(add_help=False)
parser_srv.add_argument('--hide-raw', action='store_true', help='Do not show RAW measurements in plots')
args_srv, _unknown = parser_srv.parse_known_args()
SHOW_RAW = not args_srv.hide_raw

class TimeSeriesAnalyzer:
    def __init__(self, buffer_size=1000, alpha=0.2):
        self.timing_data = deque(maxlen=buffer_size)  # Circular buffer
        self.packet_count = 0
        self.start_time = time.time()
        # EWMA parameters
        self.alpha = alpha
        self.ewma_pred = None      # EWMA prediction (µs)
        # Kalman filter state for 1-D offset
        self.kalman_est = None     # state estimate (µs)
        self.kalman_P   = 1_000_000  # estimate variance (µs²)
        self.kalman_R   = 2_000_000  # measurement noise (µs²)
        self.kalman_Q   =   10_000   # process noise (µs²)
        # PID parameters
        self.kp = 0.6   # proportional
        self.ki = 0.05  # integral
        self.kd = 0.0   # derivative
        self.pid_integral = 0
        self.pid_prev_err = None
        self.pid_pred = 0
        
    def add_measurement(self, soc_diff, fracsec_diff, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        
        # Convert to total microseconds for easier analysis
        total_microsec_diff = (soc_diff * 1000000) + fracsec_diff
        
        measurement = {
            'timestamp': timestamp,
            'soc_diff': soc_diff,
            'fracsec_diff': fracsec_diff,
            'total_microsec_diff': total_microsec_diff,
            'packet_num': self.packet_count
        }
        
        # EWMA update
        if self.ewma_pred is None:
            self.ewma_pred = total_microsec_diff
        else:
            self.ewma_pred = self.alpha * total_microsec_diff + (1 - self.alpha) * self.ewma_pred

        # Kalman filter update
        if self.kalman_est is None:
            self.kalman_est = total_microsec_diff
        # Predict
        P_pred = self.kalman_P + self.kalman_Q
        x_pred = self.kalman_est
        # Update
        K_gain = P_pred / (P_pred + self.kalman_R)
        self.kalman_est = int(x_pred + K_gain * (total_microsec_diff - x_pred))
        self.kalman_P   = int((1 - K_gain) * P_pred)

        # PID update based on bias-removed error (will subtract bias later)
        error_us = total_microsec_diff
        self.pid_integral += error_us
        derivative = 0 if self.pid_prev_err is None else (error_us - self.pid_prev_err)
        self.pid_prev_err = error_us
        self.pid_pred = int(self.kp * error_us + self.ki * self.pid_integral + self.kd * derivative)

        # Append data with predictions
        measurement['ewma_pred_us']    = int(self.ewma_pred)
        measurement['kalman_pred_us']  = int(self.kalman_est)
        measurement['pid_pred_us']     = int(self.pid_pred)

        self.timing_data.append(measurement)
        self.packet_count += 1
        
    def get_statistics(self):
        if not self.timing_data:
            return None
            
        total_diffs = [m['total_microsec_diff'] for m in self.timing_data]
        
        stats = {
            'packet_count': self.packet_count,
            'buffer_size': len(self.timing_data),
            'uptime_seconds': round(time.time() - self.start_time, 2),
            'timing_stats': {
                'min_diff_us': min(total_diffs),
                'max_diff_us': max(total_diffs),
                'avg_diff_us': round(statistics.mean(total_diffs), 2),
                'median_diff_us': round(statistics.median(total_diffs), 2),
                'std_dev_us': round(statistics.stdev(total_diffs) if len(total_diffs) > 1 else 0, 2)
            }
        }
        return stats
    
    def detect_anomalies(self, threshold_multiplier=2.0):
        if len(self.timing_data) < 10:  # Need minimum data
            return []
            
        total_diffs = [m['total_microsec_diff'] for m in self.timing_data]
        mean_diff = statistics.mean(total_diffs)
        std_dev = statistics.stdev(total_diffs) if len(total_diffs) > 1 else 0
        
        threshold = std_dev * threshold_multiplier
        anomalies = []
        
        for measurement in list(self.timing_data)[-10:]:  # Check last 10 measurements
            if abs(measurement['total_microsec_diff'] - mean_diff) > threshold:
                anomalies.append(measurement)
                
        return anomalies
    
    def get_trend_analysis(self):
        if len(self.timing_data) < 5:
            return "Insufficient data for trend analysis"
            
        recent_data = list(self.timing_data)[-20:]  # Last 20 measurements
        recent_diffs = [m['total_microsec_diff'] for m in recent_data]
        
        # Simple trend detection
        first_half = recent_diffs[:len(recent_diffs)//2]
        second_half = recent_diffs[len(recent_diffs)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg + 1000:  # 1ms threshold
            return "🔴 INCREASING latency trend detected"
        elif second_avg < first_avg - 1000:
            return "🟢 DECREASING latency trend detected"
        else:
            return "🟡 STABLE timing pattern"
    
    def save_data_summary(self):
        """Save summary to local file"""
        stats = self.get_statistics()
        if stats:
            with open('timing_analysis.json', 'w') as f:
                json.dump(stats, f, indent=2)
    
    def create_time_plot(self, save_plot=True, show_plot=False):
        """Create time series plot of timing differences"""
        if len(self.timing_data) < 2:
            print("⚠️  Need at least 2 data points for plotting")
            return
            
        # Build per-scheme paired lists (equal length)
        raw_times, raw_ms, ewma_times, ewma_ms, kalm_times, kalm_ms, pid_times, pid_ms = [],[],[],[],[],[],[],[]
        for m in self.timing_data:
            ts = datetime.fromtimestamp(m['timestamp'])
            if SHOW_RAW and m.get('scheme','raw')=='raw':
                raw_times.append(ts)
                raw_ms.append(m['total_microsec_diff']/1000.0)
            elif m.get('scheme')=='ewma':
                ewma_times.append(ts)
                ewma_ms.append(m.get('corrected_us',0)/1000.0)
            elif m.get('scheme')=='kalman':
                kalm_times.append(ts)
                kalm_ms.append(m.get('corrected_us',0)/1000.0)
            elif m.get('scheme')=='pid':
                pid_times.append(ts)
                pid_ms.append(m.get('corrected_us',0)/1000.0)
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        
        # Main timing plot
        plt.subplot(2, 1, 1)
        if SHOW_RAW and raw_times:
            plt.plot(raw_times, raw_ms,  'b-', linewidth=1.5, alpha=0.7, label='RAW')
            plt.scatter(raw_times, raw_ms, c='blue', s=15, alpha=0.4)
        if ewma_times:
            plt.plot(ewma_times, ewma_ms, 'g-', linewidth=1.5, alpha=0.7, label='EWMA')
        if kalm_times:
            plt.plot(kalm_times, kalm_ms, 'orange', linewidth=1.5, alpha=0.7, label='KALMAN')
        if pid_times:
            plt.plot(pid_times, pid_ms, 'purple', linewidth=1.5, alpha=0.7, label='PID')
        plt.title(f'🕐 Network Timing Analysis - {len(self.timing_data)} Packets', fontsize=14, fontweight='bold')
        plt.ylabel('Time Difference (milliseconds)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper right')
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.SecondLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Add statistics annotations
        if SHOW_RAW and len(raw_ms) > 1:
            avg_time = statistics.mean(raw_ms)
            std_dev = statistics.stdev(raw_ms)
            plt.axhline(y=avg_time, color='green', linestyle='--', alpha=0.7, label=f'Average: {avg_time:.2f}ms')
            plt.axhline(y=avg_time + std_dev, color='orange', linestyle=':', alpha=0.7, label=f'+1σ: {avg_time + std_dev:.2f}ms')
            plt.axhline(y=avg_time - std_dev, color='orange', linestyle=':', alpha=0.7, label=f'-1σ: {avg_time - std_dev:.2f}ms')
            plt.legend()
        
        # Histogram overlay per scheme
        plt.subplot(2, 1, 2)
        bins = 20
        if SHOW_RAW and raw_ms:
            plt.hist(raw_ms,  bins=bins, alpha=0.6, color='skyblue',  edgecolor='black', label='RAW')
        if ewma_ms:
            plt.hist(ewma_ms, bins=bins, alpha=0.6, color='lightgreen', edgecolor='black', label='EWMA')
        if kalm_ms:
            plt.hist(kalm_ms, bins=bins, alpha=0.6, color='orange',   edgecolor='black', label='KALMAN')
        if pid_ms:
            plt.hist(pid_ms, bins=bins, alpha=0.6, color='plum', edgecolor='black', label='PID')
        plt.title('📊 Timing Distribution Histogram (per scheme)', fontsize=12, fontweight='bold')
        plt.xlabel('Time Difference (milliseconds)', fontsize=10)
        plt.ylabel('Frequency', fontsize=10)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add stats text
        # choose a list that is not empty for stats
        stats_source = raw_ms if raw_ms else (ewma_ms if ewma_ms else (kalm_ms if kalm_ms else pid_ms))
        stats_text = f"""
        📈 Statistics:
        Count: {len(stats_source)}
        Min: {min(stats_source):.2f}ms
        Max: {max(stats_source):.2f}ms
        Avg: {statistics.mean(stats_source):.2f}ms
        Std: {statistics.stdev(stats_source) if len(stats_source) > 1 else 0:.2f}ms
        """
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                verticalalignment='top', fontfamily='monospace', fontsize=9)
        
        plt.tight_layout()
        
        if save_plot:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'timing_plot_{timestamp_str}.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"📈 Time plot saved as: {filename}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()  # Close to free memory
    
    def create_realtime_plot_window(self):
        """Create a real-time updating plot window"""
        def plot_updater():
            plt.ion()  # Interactive mode
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
            while True:
                if len(self.timing_data) >= 2:
                    # Clear previous plots
                    ax1.clear()
                    ax2.clear()
                    
                    # Get recent data (last 50 points for real-time view)
                    recent_data = list(self.timing_data)[-50:]
                    raw_times, raw_ms, ewma_times, ewma_ms, kalm_times, kalm_ms, pid_times, pid_ms = [],[],[],[],[],[],[],[]
                    for m in recent_data:
                        ts = datetime.fromtimestamp(m['timestamp'])
                        if m.get('scheme','raw')=='raw':
                            raw_times.append(ts)
                            raw_ms.append(m['total_microsec_diff']/1000.0)
                        elif m.get('scheme')=='ewma':
                            ewma_times.append(ts)
                            ewma_ms.append(m.get('corrected_us',0)/1000.0)
                        elif m.get('scheme')=='kalman':
                            kalm_times.append(ts)
                            kalm_ms.append(m.get('corrected_us',0)/1000.0)
                        elif m.get('scheme')=='pid':
                            pid_times.append(ts)
                            pid_ms.append(m.get('corrected_us',0)/1000.0)
                    
                    # Real-time line plot
                    if SHOW_RAW and raw_times:
                        ax1.plot(raw_times, raw_ms,  'b-', linewidth=2, label='RAW')
                        ax1.scatter(raw_times, raw_ms, c='blue', s=25, alpha=0.5)
                    if ewma_times:
                        ax1.plot(ewma_times, ewma_ms, 'g-', linewidth=2, label='EWMA')
                    if kalm_times:
                        ax1.plot(kalm_times, kalm_ms, 'orange', linewidth=2, label='KALMAN')
                    if pid_times:
                        ax1.plot(pid_times, pid_ms, 'purple', linewidth=2, label='PID')
                    ax1.set_title(f'🔄 Real-time Network Timing (Last {len(recent_data)} packets)', fontweight='bold')
                    ax1.set_ylabel('Time Difference (ms)')
                    ax1.grid(True, alpha=0.3)
                    ax1.tick_params(axis='x', rotation=45)
                    ax1.legend(loc='upper right')
                    
                    if SHOW_RAW and len(raw_ms) > 1:
                        avg_time = statistics.mean(raw_ms)
                        ax1.axhline(y=avg_time, color='green', linestyle='--', alpha=0.7)
                    
                    # Rolling statistics plot
                    if len(self.timing_data) >= 10:
                        all_raw  = [m['total_microsec_diff']/1000.0 for m in self.timing_data if SHOW_RAW and m.get('scheme','raw')=='raw']
                        all_ewma = [m.get('corrected_us',0)/1000.0 for m in self.timing_data if m.get('scheme')=='ewma']
                        all_kalm = [m.get('corrected_us',0)/1000.0 for m in self.timing_data if m.get('scheme')=='kalman']
                        all_pid = [m.get('corrected_us',0)/1000.0 for m in self.timing_data if m.get('scheme')=='pid']
                        bins = 15
                        if SHOW_RAW and all_raw:
                            ax2.hist(all_raw,  bins=bins, alpha=0.6, color='skyblue',  label='RAW')
                        ax2.hist(all_ewma, bins=bins, alpha=0.6, color='lightgreen', label='EWMA')
                        ax2.hist(all_kalm, bins=bins, alpha=0.6, color='orange',   label='KALMAN')
                        ax2.hist(all_pid, bins=bins, alpha=0.6, color='plum',   label='PID')
                        ax2.set_title('📊 Current Distribution (per scheme)')
                        ax2.set_xlabel('Time Difference (ms)')
                        ax2.set_ylabel('Count')
                        ax2.legend()
                    
                    plt.tight_layout()
                    plt.pause(2.0)  # Update every 2 seconds
                
                time.sleep(2)
        
        # Start plot updater in separate thread
        plot_thread = threading.Thread(target=plot_updater, daemon=True)
        plot_thread.start()
        print("🎬 Real-time plot window started!")

    def predicted_offset_us(self):
        return self.ewma_pred if self.ewma_pred is not None else 0

    def kalman_offset_us(self):
        return self.kalman_est if self.kalman_est is not None else 0

    def pid_offset_us(self):
        return self.pid_pred if self.pid_pred is not None else 0

if __name__ == "__main__":
    udp_server = udp_server_class.UDP_server(IP_addr='127.0.0.1',
                                            port = 12345 ,
                                            use_debugger= True,
                                            verbose_control= False,
                                            get_IPv4_override=False,
                                            create_dir=True)
    
    # Per-client analyzers and counters
    global_analyzer = TimeSeriesAnalyzer(buffer_size=2000)
    client_analyzers = {}   # key = (ip,port) -> TimeSeriesAnalyzer
    client_packet_count = {}  # key = (ip,port) -> int
    client_bias_us = {}       # key -> bias value in µs (None until determined)
    
    sqn_num = 0
    print("🚀 UDP Server with Time Series Analysis started!")
    print("📊 Real-time timing analysis enabled")
    print("📈 Plotting capabilities enabled")
    print("🎯 Listening on 127.0.0.1:12345...")
    print("=" * 60)
    
    # Ask user for plot preference
    plot_choice = input("Choose plotting option:\n1. Real-time plot window\n2. Save plots periodically\n3. Summary plot on exit\n4. No plots (console only)\nChoice (1-4): ").strip()
    
    if plot_choice == "1":
        global_analyzer.create_realtime_plot_window()
    elif plot_choice == "2":
        print("📈 Plots will be saved every 20 packets")
    elif plot_choice == "3":
        print("📊 Summary plot will be created when server stops")
    else:
        print("📊 Console-only mode selected")
    
    while True:
        try:
            #rcvd
            data_rcvd = udp_server.recv_bytes()   # tuple (SYNC, FRAME, IDCODE, SOC, FRACSEC, CHK)
            sender_key = udp_server.sender_addr  # (ip, port)

            # per-client structures
            if sender_key not in client_analyzers:
                client_analyzers[sender_key] = TimeSeriesAnalyzer(buffer_size=500)
                client_packet_count[sender_key] = 0

            client_packet_count[sender_key] += 1

            # set bias after 30 packets if not set
            if sender_key not in client_bias_us:
                client_bias_us[sender_key] = None

            scheme_id = data_rcvd[2]
            scheme_map = {1:'raw',2:'ewma',3:'kalman',4:'pid'}
            scheme = scheme_map.get(scheme_id,'raw')

            #time
            time_diff_tuple = udp_server.time_diff_calc(data_rcvd)
            
            # Add to time series analyzer
            global_analyzer.add_measurement(*time_diff_tuple)
            client_analyzers[sender_key].add_measurement(*time_diff_tuple)
            
            print(f"📦 Packet #{client_packet_count[sender_key]} - Time diff: {time_diff_tuple}")
            
            # Show analysis every 10 packets
            if client_packet_count[sender_key] % 10 == 0:
                print("\n" + "="*60)
                print("📊 TIME SERIES ANALYSIS REPORT")
                
                stats = client_analyzers[sender_key].get_statistics()
                if stats:
                    print(f"📈 Total Packets: {stats['packet_count']}")
                    print(f"⏱️  Uptime: {stats['uptime_seconds']}s")
                    print(f"📊 Timing Stats (microseconds):")
                    print(f"   Min: {stats['timing_stats']['min_diff_us']}")
                    print(f"   Max: {stats['timing_stats']['max_diff_us']}")
                    print(f"   Avg: {stats['timing_stats']['avg_diff_us']}")
                    print(f"   Std Dev: {stats['timing_stats']['std_dev_us']}")
                
                # Trend analysis
                trend = client_analyzers[sender_key].get_trend_analysis()
                print(f"📈 Trend: {trend}")
                
                # Anomaly detection
                anomalies = client_analyzers[sender_key].detect_anomalies()
                if anomalies:
                    print(f"🚨 Anomalies detected: {len(anomalies)}")
                else:
                    print("✅ No anomalies detected")
                
                print("="*60 + "\n")
                
                # Save data summary every 50 packets
                if client_packet_count[sender_key] % 50 == 0:
                    client_analyzers[sender_key].save_data_summary()
                    print(f"💾 Data summary saved to {sender_key}")
            
            # Generate plots periodically if option 2 was selected
            if plot_choice == "2" and client_packet_count[sender_key] % 20 == 0:
                client_analyzers[sender_key].create_time_plot(save_plot=True, show_plot=False)
            
            #send - Send time correction data back to client
            raw_us   = (time_diff_tuple[0] * 1_000_000) + time_diff_tuple[1]
            # store raw measurement
            global_analyzer.add_measurement(*time_diff_tuple)
            client_analyzers[sender_key].add_measurement(*time_diff_tuple)

            ewma_us  = int(global_analyzer.predicted_offset_us())
            kalm_us  = int(global_analyzer.kalman_offset_us())
            pid_us   = int(global_analyzer.pid_offset_us())

            scheme_value_map = {'raw':raw_us, 'ewma':ewma_us, 'kalman':kalm_us, 'pid':pid_us}
            chosen_us = scheme_value_map.get(scheme, raw_us)

            # apply bias only for EWMA, KALMAN, or PID schemes
            if scheme in ('ewma','kalman','pid') and client_bias_us[sender_key] is not None:
                chosen_us -= client_bias_us[sender_key]

            # annotate latest measurement with scheme and corrected value
            for ana in (global_analyzer, client_analyzers[sender_key]):
                if ana.timing_data:
                    ana.timing_data[-1]['scheme'] = scheme
                    ana.timing_data[-1]['corrected_us'] = chosen_us

            correction_data = {
                'ack_num': sqn_num,
                'scheme': scheme,
                'correction_us': chosen_us,
                'server_time_soc': int(time.time()),
                'server_time_fracsec': int((time.time() % 1) * 1_000_000)
            }
            correction_json = json.dumps(correction_data)
            udp_server.send_ack(correction_json)
            bias_info = f" (bias {client_bias_us[sender_key]} µs)" if client_bias_us[sender_key] is not None and scheme in ('ewma','kalman','pid') else ""
            print(f"📤 Reply to {scheme.upper()} client {sender_key} pkt#{client_packet_count[sender_key]} → {chosen_us} µs{bias_info}")
            sqn_num = sqn_num + 1
        except struct.error as e:
            print(f"Invalid packet format received, ignoring: {e}")
            continue
        except KeyboardInterrupt:
            print("\nUDP Server stopped by user")
            if plot_choice == "3":
                print("💾 Generating summary plot before exit...")
                global_analyzer.create_time_plot(save_plot=True, show_plot=False)
            break
        except Exception as e:
            print(f"Error processing packet: {e}")
            continue