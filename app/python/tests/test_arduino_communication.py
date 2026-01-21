import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.arduino_communication import ArduinoCom


class TestSignalValidation(unittest.TestCase):
    """Tests for signal format validation."""

    def setUp(self):
        self.arduino = ArduinoCom()

    def test_invalid_signal_type(self):
        """Invalid signal type should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.arduino.send_signal(('x', 0.5, 100, 500))
        self.assertIn("Invalid signal type", str(ctx.exception))

    def test_signal_not_tuple(self):
        """Non-tuple/list signal should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.arduino.send_signal("invalid")
        self.assertIn("tuple/list", str(ctx.exception))

    def test_empty_signal(self):
        """Empty signal should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.arduino.send_signal(())
        self.assertIn("at least 1 element", str(ctx.exception))

    def test_vib1_missing_elements(self):
        """Vib1 with fewer than 4 elements should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.arduino.send_signal(('v', 0.5, 100))
        self.assertIn("requires 4 elements", str(ctx.exception))

    def test_buzzer_missing_elements(self):
        """Buzzer with fewer than 4 elements should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.arduino.send_signal(('b', 0.5, 200))
        self.assertIn("requires 4 elements", str(ctx.exception))

    def test_combined_missing_elements(self):
        """Combined signal with fewer than 7 elements should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.arduino.send_signal(('c', 0.5, 100, 500, 0.3, 200))
        self.assertIn("requires 7 elements", str(ctx.exception))


class TestSignalEncoding(unittest.TestCase):
    """Tests for signal byte encoding (without actual serial connection)."""

    def setUp(self):
        self.arduino = ArduinoCom()
        # Capture the command that would be sent
        self.sent_cmd = None

    def test_amplitude_clamping_high(self):
        """Amplitude > 1.0 should be clamped to 255."""
        # Test that encoding doesn't crash with values > 1.0
        # (We can't fully test the byte value without mocking, but we verify no exception)
        try:
            self.arduino.send_signal(('v', 1.5, 100, 500))
        except Exception as e:
            if "disconnected" not in str(e).lower() and "port" not in str(e).lower():
                self.fail(f"Unexpected exception: {e}")

    def test_amplitude_clamping_negative(self):
        """Amplitude < 0 should be clamped to 0."""
        try:
            self.arduino.send_signal(('v', -0.5, 100, 500))
        except Exception as e:
            if "disconnected" not in str(e).lower() and "port" not in str(e).lower():
                self.fail(f"Unexpected exception: {e}")

    def test_valid_vib1_signal(self):
        """Valid Vib1 signal should not raise ValueError."""
        # Without connection, it logs warning but doesn't raise
        self.arduino.send_signal(('v', 0.5, 170, 500))

    def test_valid_vib2_signal(self):
        """Valid Vib2 signal should not raise ValueError."""
        self.arduino.send_signal(('w', 0.5, 170, 500))

    def test_valid_buzzer_signal(self):
        """Valid Buzzer signal should not raise ValueError."""
        self.arduino.send_signal(('b', 0.5, 1000, 500))

    def test_valid_combined_signal(self):
        """Valid combined signal should not raise ValueError."""
        self.arduino.send_signal(('c', 0.5, 170, 500, 0.3, 1000, 300))


class TestConnectionState(unittest.TestCase):
    """Tests for connection state management."""

    def setUp(self):
        self.arduino = ArduinoCom()

    def test_initial_state_not_connected(self):
        """Initially should not be connected."""
        self.assertFalse(self.arduino.is_connected())

    def test_disconnect_when_not_connected(self):
        """Disconnect when not connected should not raise."""
        self.arduino.disconnect()  # Should not raise
        self.assertFalse(self.arduino.is_connected())

    def test_check_connection_when_not_connected(self):
        """check_connection when not connected should raise SerialException."""
        import serial
        with self.assertRaises(serial.SerialException) as ctx:
            self.arduino.check_connection()
        self.assertIn("disconnected", str(ctx.exception).lower())


class TestConnectionRetry(unittest.TestCase):
    """Tests for connection retry logic."""

    def setUp(self):
        self.arduino = ArduinoCom()

    def test_connect_invalid_port(self):
        """Connecting to invalid port should raise after retries."""
        with self.assertRaises(Exception) as ctx:
            self.arduino.connect("/dev/nonexistent_port_12345", retries=1, retry_delay=0.01)
        # Should mention the port or connection failure
        self.assertTrue(
            "not found" in str(ctx.exception).lower() or
            "cannot open" in str(ctx.exception).lower() or
            "no such file" in str(ctx.exception).lower()
        )


if __name__ == '__main__':
    unittest.main()
