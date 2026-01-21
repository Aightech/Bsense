import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.experiment import Experiment


class TestExperimentSchemaValidation(unittest.TestCase):
    """Tests for JSON schema validation."""

    def setUp(self):
        self.exp = Experiment()

    def tearDown(self):
        self.exp.close()

    def test_valid_sequence(self):
        """Valid sequence should load without error."""
        rules = {
            "Type": "Sequence",
            "Repeat": 2,
            "Content": [
                {"Type": "Delay", "Duration": 1.0}
            ]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 2)

    def test_missing_type_field(self):
        """Missing Type field should raise ValueError."""
        rules = {"Repeat": 2, "Content": []}
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Type", str(ctx.exception))

    def test_sequence_missing_repeat(self):
        """Sequence without Repeat should raise ValueError."""
        rules = {"Type": "Sequence", "Content": []}
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Repeat", str(ctx.exception))

    def test_sequence_missing_content(self):
        """Sequence without Content should raise ValueError."""
        rules = {"Type": "Sequence", "Repeat": 1}
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Content", str(ctx.exception))

    def test_negative_repeat(self):
        """Negative Repeat should raise ValueError."""
        rules = {"Type": "Sequence", "Repeat": -1, "Content": []}
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("non-negative", str(ctx.exception))

    def test_delay_missing_duration(self):
        """Delay without Duration should raise ValueError."""
        rules = {"Type": "Delay"}
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Duration", str(ctx.exception))

    def test_unknown_type(self):
        """Unknown type should raise ValueError."""
        rules = {"Type": "InvalidType"}
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Unknown type", str(ctx.exception))


class TestStimulusValidation(unittest.TestCase):
    """Tests for stimulus schema validation."""

    def setUp(self):
        self.exp = Experiment()

    def tearDown(self):
        self.exp.close()

    def test_valid_buzzer(self):
        """Valid buzzer stimulus should load."""
        rules = {
            "Type": "stimulus",
            "Content": [{"Type": "Buzzer", "Amplitude": 0.5}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 1)

    def test_buzzer_missing_amplitude(self):
        """Buzzer without Amplitude should raise ValueError."""
        rules = {
            "Type": "stimulus",
            "Content": [{"Type": "Buzzer"}]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Amplitude", str(ctx.exception))

    def test_valid_vib1(self):
        """Valid Vib1 stimulus should load."""
        rules = {
            "Type": "stimulus",
            "Content": [{"Type": "Vib1", "Amplitude": 0.5, "Frequency": 170, "Duration": 100}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 1)

    def test_vib1_missing_frequency(self):
        """Vib1 without Frequency should raise ValueError."""
        rules = {
            "Type": "stimulus",
            "Content": [{"Type": "Vib1", "Amplitude": 0.5, "Duration": 100}]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Frequency", str(ctx.exception))

    def test_unknown_stimulus_type(self):
        """Unknown stimulus type should raise ValueError."""
        rules = {
            "Type": "stimulus",
            "Content": [{"Type": "InvalidStim", "Amplitude": 0.5}]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Unknown stimulus type", str(ctx.exception))


class TestDropoutSequenceValidation(unittest.TestCase):
    """Tests for dropout sequence validation."""

    def setUp(self):
        self.exp = Experiment()

    def tearDown(self):
        self.exp.close()

    def test_valid_dropout(self):
        """Valid dropout sequence should load."""
        rules = {
            "Type": "Dropout_sequence",
            "Number_drop": 1,
            "Repeat": 3,
            "Content": [{"Type": "Delay", "Duration": 1.0}],
            "Dropout_content": [{"Type": "Delay", "Duration": 0.5}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 3)

    def test_dropout_exceeds_repeat(self):
        """Number_drop > Repeat should raise ValueError."""
        rules = {
            "Type": "Dropout_sequence",
            "Number_drop": 5,
            "Repeat": 3,
            "Content": [{"Type": "Delay", "Duration": 1.0}],
            "Dropout_content": [{"Type": "Delay", "Duration": 0.5}]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("cannot exceed", str(ctx.exception))


class TestExperimentControl(unittest.TestCase):
    """Tests for experiment start/stop/pause."""

    def setUp(self):
        self.exp = Experiment()
        self.exp.from_dict({
            "Type": "Sequence",
            "Repeat": 1,
            "Content": [{"Type": "Delay", "Duration": 0.1}]
        })

    def tearDown(self):
        self.exp.close()

    def test_start_sets_running(self):
        """Start should set running to True."""
        self.assertFalse(self.exp.running)
        self.exp.start()
        self.assertTrue(self.exp.running)
        self.exp.stop()

    def test_stop_resets_index(self):
        """Stop should reset current_idx to 0."""
        self.exp.current_idx = 5
        self.exp.stop()
        self.assertEqual(self.exp.current_idx, 0)

    def test_pause_does_not_reset_index(self):
        """Pause should not reset current_idx."""
        self.exp.current_idx = 2
        self.exp.pause()
        self.assertEqual(self.exp.current_idx, 2)


if __name__ == '__main__':
    unittest.main()
