import math
import socket
import tempfile
import unittest
from pathlib import Path
from haptisense.bench import BenchController, decode_ack, encode_pwm, serve, validate_packet


class BenchTests(unittest.TestCase):
    def test_defaults(self): self.assertEqual(validate_packet({})["ny"], 1)
    def test_non_object(self):
        for v in (None, [], "", 5):
            with self.subTest(v=v), self.assertRaises(ValueError): validate_packet(v)
    def test_nonfinite(self):
        for v in (math.nan, math.inf, -math.inf):
            with self.subTest(v=v), self.assertRaises(ValueError): validate_packet({"vx": v})
    def test_strings_and_bools(self):
        for v in ("1", True):
            with self.subTest(v=v), self.assertRaises(ValueError): validate_packet({"vx": v})
    def test_negative_penetration(self):
        with self.assertRaises(ValueError): validate_packet({"penetration_m": -.1})
    def test_overlarge_penetration(self):
        with self.assertRaises(ValueError): validate_packet({"penetration_m": .06})
    def test_normal(self):
        with self.assertRaises(ValueError): validate_packet({"nx": 0, "ny": 0, "nz": 0})
    def test_unknown_texture(self):
        with self.assertRaises(ValueError): validate_packet({"texture": []})
    def test_pwm_endpoints(self):
        self.assertEqual(encode_pwm(1, 0), b"H1,1,0\n")
        self.assertEqual(encode_pwm(2, 1), b"H1,2,64\n")
    def test_pwm_limit(self):
        for cap in (65, -1, True, 3.1):
            with self.subTest(cap=cap), self.assertRaises(ValueError): encode_pwm(1, .5, cap)
    def test_pwm_sequence(self):
        with self.assertRaises(ValueError): encode_pwm(-1, 0)
    def test_pwm_nonfinite(self):
        with self.assertRaises(ValueError): encode_pwm(1, math.nan)
    def test_ack(self):
        self.assertEqual(decode_ack(b"A1,1,32,512,200\r\n")["adc_raw"], 512)
    def test_bad_ack(self):
        for s in (b"", b"A1,1,65,0,0", b"A1,1,0,1024,0", b"\xff", b"A1,1,0,0,0,0"):
            with self.subTest(s=s), self.assertRaises(ValueError): decode_ack(s)
    def test_starts_stopped(self):
        self.assertEqual(BenchController().wire(1), b"H1,1,0\n")
    def test_contact_then_stale(self):
        b = BenchController(); b.receive({"penetration_m": .004, "vx": .04}, 1)
        self.assertGreater(int(b.wire(1.01).decode().strip().split(",")[-1]), 0)
        self.assertEqual(int(b.wire(1.11).decode().strip().split(",")[-1]), 0)
    def test_lift_off_immediate_stop(self):
        b = BenchController(); b.receive({"penetration_m": .004}, 1)
        b.receive({"penetration_m": 0, "ax": 10}, 1.02)
        self.assertEqual(b.amplitude, 0)
    def test_invalid_stops(self):
        b = BenchController(); b.receive({"penetration_m": .004}, 1)
        with self.assertRaises(ValueError): b.receive({"vx": math.nan}, 1.01)
        self.assertEqual(b.amplitude, 0)
    def test_backwards_time_stops(self):
        b = BenchController(); b.receive({"penetration_m": .004}, 2)
        with self.assertRaises(ValueError): b.receive({}, 1)
        self.assertEqual(b.amplitude, 0)
    def test_timeout_configuration(self):
        with self.assertRaises(ValueError): BenchController(stale_s=0)
    def test_physical_requires_arm(self):
        with self.assertRaises(ValueError): serve("unused.csv", 1, serial_port="COM3")
    def test_arm_requires_physical(self):
        with self.assertRaises(ValueError): serve("unused.csv", 1, arm=True)
    def test_no_evidence_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "run.csv"; p.touch()
            with self.assertRaises(FileExistsError): serve(str(p), .01)
    def test_mock_session(self):
        with tempfile.TemporaryDirectory() as d, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
            p = Path(d) / "run.csv"; serve(str(p), .03, port=port)
            self.assertIn("mock_no_hardware", p.read_text())
            self.assertNotIn("physical_serial_ack", p.read_text())
