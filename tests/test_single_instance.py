from __future__ import annotations

import os
import threading
import unittest

from ryzen_temp_limit.single_instance import (
    ActivationServer,
    SingleInstance,
    signal_activation,
)


@unittest.skipUnless(os.name == "nt", "Windows only")
class SingleInstanceTests(unittest.TestCase):
    def test_second_instance_is_detected(self) -> None:
        name = f"Local\\RyzenTempLimit.Test.{os.getpid()}"
        first = SingleInstance(name)
        second = SingleInstance(name)
        try:
            self.assertFalse(first.already_running)
            self.assertTrue(second.already_running)
        finally:
            second.release()
            first.release()


@unittest.skipUnless(os.name == "nt", "Windows only")
class ActivationTests(unittest.TestCase):
    def test_signal_reaches_the_server(self) -> None:
        name = f"Local\\RyzenTempLimit.Activate.Test.{os.getpid()}"
        fired = threading.Event()
        server = ActivationServer(fired.set, name=name)
        server.start()
        try:
            self.assertTrue(signal_activation(name))
            self.assertTrue(fired.wait(3))
        finally:
            server.stop()

    def test_signal_without_a_server(self) -> None:
        self.assertFalse(signal_activation(f"Local\\RyzenTempLimit.Missing.{os.getpid()}"))


if __name__ == "__main__":
    unittest.main()
