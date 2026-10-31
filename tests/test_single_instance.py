from __future__ import annotations

import os
import unittest

from ryzen_temp_limit.single_instance import SingleInstance


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


if __name__ == "__main__":
    unittest.main()
