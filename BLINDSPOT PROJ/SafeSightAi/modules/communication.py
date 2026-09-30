import socket
import json
import logging
import threading

logger = logging.getLogger(__name__)

class WearableCommunicator:
    def __init__(self, config=None):
        """
        Args:
            config (dict): Configurations containing:
                - mode (str): Communication mode - 'serial', 'udp', or 'both'. Default: 'serial'
                - serial_port (str): Serial port for ESP32, e.g. 'COM8'
                - serial_baud (int): Baud rate, default 74880 (for 26MHz XTAL ESP32)
                - base_ip (str): Starting IP address, e.g. '192.168.1.100'
                - udp_host (str): loopback host to send simulated UDP packets to, default '127.0.0.1'
                - udp_port (int): loopback port, default 5005
        """
        if config is None:
            config = {}
            
        self.mode = config.get("mode", "serial")
        self.base_ip = config.get("base_ip", "192.168.1.100")
        self.udp_host = config.get("udp_host", "127.0.0.1")
        self.udp_port = config.get("udp_port", 5005)
        self.serial_port = config.get("serial_port", "COM8")
        self.serial_baud = config.get("serial_baud", 74880)
        
        # Track latest ultrasonic distance from ESP32
        self.latest_distance = -1.0
        self.last_distance_time = 0.0
        self._last_sent_zone = {}

        # Initialize UDP socket for loopback simulation
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Initialize Serial connection to ESP32
        self.ser = None
        self._serial_lock = threading.Lock()
        if self.mode in ("serial", "both"):
            self._init_serial()
        
        logger.info(f"WearableCommunicator initialized. Mode={self.mode}, "
                    f"Serial={self.serial_port}@{self.serial_baud}, "
                    f"UDP={self.udp_host}:{self.udp_port}")

    def _init_serial(self):
        """Initialize serial connection to ESP32."""
        try:
            import serial
            self.ser = serial.Serial(
                self.serial_port,
                self.serial_baud,
                timeout=0.1,
                dsrdtr=False,
                rtscts=False
            )
            # Prevent DTR/RTS from resetting ESP32
            self.ser.setDTR(False)
            self.ser.setRTS(False)
            logger.info(f"Serial connection established: {self.serial_port} @ {self.serial_baud} baud")
            
            # Start background reader for ESP32 responses
            self._reader_thread = threading.Thread(target=self._serial_reader, daemon=True)
            self._reader_thread.start()
        except ImportError:
            logger.warning("pyserial not installed. Run: pip install pyserial")
            self.ser = None
        except Exception as e:
            logger.warning(f"Failed to open serial port {self.serial_port}: {e}")
            self.ser = None

    def _serial_reader(self):
        """Background thread to read and log ESP32 responses."""
        import time as _time
        while self.ser and self.ser.is_open:
            try:
                line = self.ser.readline()
                if line:
                    text = line.decode('utf-8', errors='ignore').strip()
                    if text:
                        if text.startswith("{"):
                            try:
                                data = json.loads(text)
                                if "distance_cm" in data:
                                    dist = float(data["distance_cm"])
                                    if dist > 0:
                                        self.latest_distance = dist
                                        self.last_distance_time = _time.time()
                            except Exception:
                                pass
                        logger.debug(f"ESP32: {text}")
            except Exception:
                break

    def get_latest_distance(self, max_age=1.5):
        """Returns the most recent valid ultrasonic distance in cm, or -1.0 if unavailable/stale."""
        import time as _time
        if (_time.time() - getattr(self, 'last_distance_time', 0.0)) <= max_age:
            return getattr(self, 'latest_distance', -1.0)
        return -1.0

    def get_device_ip(self, worker_id):
        """
        Maps worker tracker ID to simulated IP address dynamically.
        """
        try:
            octets = self.base_ip.split(".")
            prefix = ".".join(octets[:3])
            last_octet = int(octets[3])
            return f"{prefix}.{last_octet + worker_id}"
        except Exception as e:
            logger.warning(f"Error calculating IP for worker ID {worker_id}: {e}. Falling back to base IP.")
            return self.base_ip

    def send_alert(self, worker_id, zone):
        """
        Sends warning alert signals to the worker's wearable ESP32 device.
        Supports both Serial (USB) and UDP transmission modes.
        
        Args:
            worker_id (int): Persistent tracker ID.
            zone (str): Threat zone ('SAFE', 'WARNING', 'DANGER', 'CRITICAL').
            
        Returns:
            dict: The alert packet payload.
        """
        device_ip = self.get_device_ip(worker_id)
        
        # Map safety zone status to device actions
        if zone == "WARNING":
            vibration = "single_pulse"
            light = "off"
            sound = "off"
        elif zone == "DANGER":
            vibration = "pulsed"
            light = "flashing"
            sound = "off"
        elif zone == "CRITICAL":
            vibration = "continuous_high"
            light = "flashing_red"
            sound = "on"
        else:  # SAFE
            vibration = "off"
            light = "off"
            sound = "off"

        payload = {
            "worker_id": worker_id,
            "device_ip": device_ip,
            "zone": zone,
            "vibration": vibration,
            "light": light,
            "sound": sound
        }

        # Transmit alert: always send when zone is active (non-SAFE), or when transitioning back to SAFE
        prev_zone = self._last_sent_zone.get(worker_id)
        should_send = (zone != "SAFE") or (prev_zone is not None and prev_zone != "SAFE")
        if should_send:
            self._last_sent_zone[worker_id] = zone
            msg = json.dumps(payload).encode("utf-8")
            
            # Send via Serial to ESP32
            if self.mode in ("serial", "both"):
                self._send_serial(msg, payload)
            
            # Send via UDP (loopback or network)
            if self.mode in ("udp", "both"):
                self._send_udp(msg, device_ip, payload)

        return payload

    def _send_serial(self, msg, payload):
        """Send alert via Serial (USB) to ESP32."""
        if self.ser and self.ser.is_open:
            try:
                with self._serial_lock:
                    self.ser.write(msg + b'\n')
                    self.ser.flush()
                logger.debug(f"Serial Alert Sent -> ESP32: {payload}")
            except Exception as e:
                logger.debug(f"Failed to send serial alert: {e}")
                # Attempt reconnection
                self._init_serial()
        else:
            logger.debug("Serial port not available, skipping serial alert")

    def _send_udp(self, msg, device_ip, payload):
        """Send alert via UDP socket."""
        try:
            self.sock.sendto(msg, (self.udp_host, self.udp_port))
            logger.debug(f"UDP Alert Sent -> {device_ip}: {payload}")
        except Exception as e:
            logger.debug(f"Failed to transmit UDP packet to {self.udp_host}:{self.udp_port}: {e}")

    def close(self):
        """Clean up resources."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Serial connection closed")
        try:
            self.sock.close()
        except Exception:
            pass
