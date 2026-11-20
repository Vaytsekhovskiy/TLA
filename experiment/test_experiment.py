"""Regression checks for the experiment runner and refinement comparison."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compare_experiment import check_refinement, graph_delta, read_graph
from run_experiment import EXPERIMENT, TASKS, extract_module, generate, verify


class ExtractionTests(unittest.TestCase):
    def test_extraction_preserves_module_text(self):
        module = "---- MODULE Example ----\nVARIABLE x\nInit == x = 0\n====\n"
        fence = chr(96) * 3
        self.assertEqual(extract_module(f"Here is the result\n{fence}tla\n{module}{fence}"), module)

    def test_invalid_text_is_preserved_for_sany(self):
        invalid = "module Example\nPRED Init == TRUE\nEND MODULE"
        self.assertEqual(extract_module(invalid), invalid)

    def test_missing_terminator_remains_an_error(self):
        incomplete = "---- MODULE Example ----\nInit == TRUE"
        self.assertEqual(extract_module("Some text\n" + incomplete), incomplete)


class CheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.java = shutil.which("java")
        local_java = Path("C:/Program Files/Java/jdk-22.0.2/bin/java.exe")
        if local_java.is_file():
            cls.java = str(local_java)
        if cls.java is None:
            raise unittest.SkipTest("Java is required for integration checks")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=EXPERIMENT)
        self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_invalid_sany_output_cannot_pass(self):
        module = self.directory / "Invalid.tla"
        module.write_text("---- MODULE Invalid ----\nInit == MissingOperator\n====\n", encoding="utf-8")
        cfg = self.directory / "Invalid.cfg"
        cfg.write_text("INIT Init\nNEXT Next\n", encoding="utf-8")
        status, _ = verify(self.java, module, cfg, self.directory / "invalid")
        self.assertFalse(status["sany"])
        self.assertIsNone(status["tlc"])

    def test_resume_verifies_saved_response_without_requesting_another(self):
        task = self.directory / "92_ConfigParams"
        attempt = task / "01"
        attempt.mkdir(parents=True)
        shutil.copyfile(EXPERIMENT / "gold/ConfigParams.cfg", task / "ConfigParams.cfg")
        answer = (EXPERIMENT / "generated/ConfigParamsLLM.tla").read_text(encoding="utf-8")
        (attempt / "request.json").write_text("{}", encoding="utf-8")
        (attempt / "response.json").write_text(json.dumps({
            "message": {"content": answer}, "done_reason": "stop",
        }), encoding="utf-8")
        with patch("run_experiment.ollama", side_effect=AssertionError("Unexpected API call")):
            result = generate(
                self.java, "test-model", self.directory, "ConfigParams",
                TASKS["ConfigParams"], False, "chat", {},
            )
        self.assertEqual(len(result["attempts"]), 1)
        self.assertTrue(result["attempts"][0]["tlc"])
        self.assertEqual((task / "ConfigParamsLLM.tla").read_text(encoding="utf-8"), answer)

    def test_behavior_comparison_detects_a_changed_transition(self):
        gold = self.directory / "Test1623.tla"
        candidate = self.directory / "Mutant.tla"
        cfg = self.directory / "Test1623.cfg"
        shutil.copyfile(EXPERIMENT / "gold" / gold.name, gold)
        shutil.copyfile(EXPERIMENT / "gold" / cfg.name, cfg)
        candidate.write_text(
            "---- MODULE Mutant ----\nEXTENDS Integers\nCONSTANT N\nVARIABLE x\n"
            "Init == x = N\nNext == x' = x + 1\n====\n",
            encoding="utf-8",
        )
        status = check_refinement(
            self.java, self.directory / "comparison", candidate, gold, cfg, {"x": "x"}, False, "Gold",
        )
        self.assertTrue(status["sany"])
        self.assertFalse(status["tlc"])
        self.assertIn("violated", (self.directory / "comparison/tlc.txt").read_text(encoding="utf-8"))

    def test_stuttering_candidate_requires_reverse_comparison(self):
        gold = self.directory / "Test1623.tla"
        candidate = self.directory / "Stutter.tla"
        cfg = self.directory / "Test1623.cfg"
        shutil.copyfile(EXPERIMENT / "gold" / gold.name, gold)
        shutil.copyfile(EXPERIMENT / "gold" / cfg.name, cfg)
        candidate.write_text(
            "---- MODULE Stutter ----\nEXTENDS Integers\nCONSTANT N\nVARIABLE x\n"
            "Init == x = N\nNext == UNCHANGED x\n====\n",
            encoding="utf-8",
        )
        forward = check_refinement(
            self.java, self.directory / "forward", candidate, gold, cfg, {"x": "x"}, False, "Gold",
        )
        reverse = check_refinement(
            self.java, self.directory / "reverse", gold, candidate, cfg, {"x": "x"}, False, "Model",
        )
        self.assertTrue(forward["tlc"])
        self.assertFalse(reverse["tlc"])
        graphs = {}
        for label, module in (("gold", gold), ("model", candidate)):
            dot = self.directory / f"{label}.dot"
            status, _ = verify(self.java, module, cfg, self.directory / label, dump=dot)
            graphs[label] = read_graph(dot, ("x",), status["metrics"]["distinct"])
        delta = graph_delta(graphs["gold"], graphs["model"])
        self.assertEqual(delta["states"]["gold_only"], 4)
        self.assertEqual(delta["states"]["model_only"], 0)


if __name__ == "__main__":
    unittest.main()
