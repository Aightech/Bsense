import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.experiment import Experiment


class TestCaseInsensitivity(unittest.TestCase):
    """Tests for case-insensitive protocol parsing."""

    def setUp(self):
        self.exp = Experiment()

    def tearDown(self):
        self.exp.close()

    def test_lowercase_type(self):
        """Lowercase 'type' should work."""
        rules = {
            "type": "sequence",
            "repeat": 2,
            "content": [{"type": "delay", "duration": 1.0}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 2)

    def test_uppercase_type(self):
        """Uppercase 'TYPE' should work."""
        rules = {
            "TYPE": "SEQUENCE",
            "REPEAT": 2,
            "CONTENT": [{"TYPE": "DELAY", "DURATION": 1.0}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 2)

    def test_mixed_case(self):
        """Mixed case should work."""
        rules = {
            "Type": "sequence",
            "REPEAT": 2,
            "content": [{"type": "Delay", "Duration": 1.0}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 2)

    def test_lowercase_stimulus(self):
        """Lowercase stimulus types should work."""
        rules = {
            "type": "stimulus",
            "content": [{"type": "vib1", "amplitude": 0.5, "frequency": 170, "duration": 100}]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 1)

    def test_lowercase_randomized_sequence(self):
        """Lowercase randomized_sequence should work."""
        self.exp.log_cb = lambda x: None  # suppress log
        rules = {
            "type": "randomized_sequence",
            "max_consecutive": 2,
            "stimuli": [
                {"repeat": 2, "content": {"type": "vib1", "amplitude": 0.33, "frequency": 170, "duration": 100}},
                {"repeat": 2, "content": {"type": "vib1", "amplitude": 1.0, "frequency": 170, "duration": 100}}
            ]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 4)


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


class TestRandomizedSequenceValidation(unittest.TestCase):
    """Tests for Randomized_sequence schema validation."""

    def setUp(self):
        self.exp = Experiment()
        # Suppress log output during tests
        self.exp.log_cb = lambda x: None

    def tearDown(self):
        self.exp.close()

    def test_valid_randomized_sequence(self):
        """Valid Randomized_sequence should load."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2,
            "Stimuli": [
                {"Repeat": 3, "Label": "Low", "Content": {"Type": "Vib1", "Amplitude": 0.33, "Frequency": 170, "Duration": 100}},
                {"Repeat": 3, "Label": "High", "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        self.exp.from_dict(rules)
        # 6 stimuli total (3 + 3), no delays between
        self.assertEqual(len(self.exp.sequence), 6)

    def test_randomized_with_delay(self):
        """Randomized_sequence with Delay should include delays."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2,
            "Delay": {"Type": "Delay", "Duration": 1.0},
            "Stimuli": [
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 0.5, "Frequency": 170, "Duration": 100}},
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        self.exp.from_dict(rules)
        # 4 stimuli + 3 delays between them = 7 events
        self.assertEqual(len(self.exp.sequence), 7)

    def test_randomized_missing_max_consecutive(self):
        """Randomized_sequence without Max_consecutive should raise."""
        rules = {
            "Type": "Randomized_sequence",
            "Stimuli": [
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 0.5, "Frequency": 170, "Duration": 100}},
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Max_consecutive", str(ctx.exception))

    def test_randomized_missing_stimuli(self):
        """Randomized_sequence without Stimuli should raise."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Stimuli", str(ctx.exception))

    def test_randomized_only_one_stimulus_type(self):
        """Randomized_sequence with only 1 stimulus type should raise."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2,
            "Stimuli": [
                {"Repeat": 5, "Content": {"Type": "Vib1", "Amplitude": 0.5, "Frequency": 170, "Duration": 100}}
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("at least 2", str(ctx.exception))

    def test_randomized_invalid_max_consecutive(self):
        """Randomized_sequence with Max_consecutive < 1 should raise."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 0,
            "Stimuli": [
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 0.5, "Frequency": 170, "Duration": 100}},
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("positive integer", str(ctx.exception))

    def test_randomized_stimulus_missing_repeat(self):
        """Stimuli item without Repeat should raise."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2,
            "Stimuli": [
                {"Content": {"Type": "Vib1", "Amplitude": 0.5, "Frequency": 170, "Duration": 100}},
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Repeat", str(ctx.exception))

    def test_randomized_stimulus_missing_content(self):
        """Stimuli item without Content should raise."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2,
            "Stimuli": [
                {"Repeat": 2},
                {"Repeat": 2, "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            self.exp.from_dict(rules)
        self.assertIn("Content", str(ctx.exception))


class TestRandomizedSequenceConstraint(unittest.TestCase):
    """Tests for max consecutive constraint enforcement."""

    def setUp(self):
        self.exp = Experiment()
        self.exp.log_cb = lambda x: None

    def tearDown(self):
        self.exp.close()

    def test_max_consecutive_enforced(self):
        """Check that max consecutive constraint is satisfied."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 2,
            "Stimuli": [
                {"Repeat": 10, "Label": "A", "Content": {"Type": "Vib1", "Amplitude": 0.33, "Frequency": 170, "Duration": 100}},
                {"Repeat": 10, "Label": "B", "Content": {"Type": "Vib1", "Amplitude": 0.66, "Frequency": 170, "Duration": 100}},
                {"Repeat": 10, "Label": "C", "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        self.exp.from_dict(rules)

        # Check that no label appears more than 2 times consecutively
        consecutive = 1
        prev_label = None
        for event in self.exp.sequence:
            label = event[1]  # the label is stored in position 1
            if label == prev_label:
                consecutive += 1
                self.assertLessEqual(consecutive, 2, f"Found {consecutive} consecutive '{label}' events")
            else:
                consecutive = 1
            prev_label = label

    def test_total_count_preserved(self):
        """Check that total stimulus count is preserved after randomization."""
        rules = {
            "Type": "Randomized_sequence",
            "Max_consecutive": 3,
            "Stimuli": [
                {"Repeat": 20, "Label": "33%", "Content": {"Type": "Vib1", "Amplitude": 0.33, "Frequency": 170, "Duration": 100}},
                {"Repeat": 20, "Label": "66%", "Content": {"Type": "Vib1", "Amplitude": 0.66, "Frequency": 170, "Duration": 100}},
                {"Repeat": 20, "Label": "100%", "Content": {"Type": "Vib1", "Amplitude": 1.0, "Frequency": 170, "Duration": 100}}
            ]
        }
        self.exp.from_dict(rules)
        self.assertEqual(len(self.exp.sequence), 60)

        # Count each label
        counts = {}
        for event in self.exp.sequence:
            label = event[1]
            counts[label] = counts.get(label, 0) + 1

        self.assertEqual(counts.get("33%", 0), 20)
        self.assertEqual(counts.get("66%", 0), 20)
        self.assertEqual(counts.get("100%", 0), 20)


if __name__ == '__main__':
    unittest.main()
