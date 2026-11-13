import copy
import math
import unittest

from acceptance_rounds import CHECKS, evaluate, plan_sha256


class AcceptanceRoundsTests(unittest.TestCase):
    def setUp(self):
        self.plan = {"schema_version": 1, "rubric_id": "fixed-v1", "tasks": [
            {"id": "zh-1", "language": "zh", "group": "knowledge", "kind": "knowledge", "prompt": "question",
             "rubric": "predeclared substantive correctness", "checks": list(CHECKS)}]}

    def result(self, mid="mic-1", seconds=1.9):
        return {"id": "zh-1", "response": "substantive answer", "answer_kind": "answer", "errors": [], "guessed": False,
                "checks": {k: {"status": "pass", "reason": "rubric met", "evidence": "review.txt#1"} for k in CHECKS},
                "acoustic": {"status": "measured", "seconds": seconds, "method": "microphone_acoustic",
                             "start_event": "user_speech_end", "end_event": "first_substantive_audible_response",
                             "evidence": "capture.wav#0.0-1.9", "measurement_id": mid}}

    def round(self, result=None, index=0):
        return {"index": index, "plan_sha256": plan_sha256(self.plan), "results": [self.result() if result is None else result]}

    def verdict(self, result):
        return evaluate(self.plan, [self.round(result)])

    def test_complete_correct_acoustic_pass_including_boundary(self):
        for seconds in (0, 2):
            self.assertEqual(self.verdict(self.result(seconds=seconds))["overall"], "pass")

    def test_missing_planned_item_never_passes(self):
        row = self.round(); row["results"] = []
        report = evaluate(self.plan, [row])
        self.assertEqual(report["overall"], "unmeasured")
        self.assertEqual(report["rounds"][0]["coverage"]["missing"], ["zh-1"])

    def test_every_item_not_average_or_p90(self):
        extra = copy.deepcopy(self.plan["tasks"][0]); extra["id"] = "en-2"; extra["language"] = "en"
        self.plan["tasks"].append(extra)
        good = self.result(seconds=.1); bad = self.result(mid="mic-2", seconds=2.001); bad["id"] = "en-2"
        row = self.round(good); row["results"].append(bad)
        self.assertEqual(evaluate(self.plan, [row])["overall"], "fail")

    def test_nonfinite_negative_bool_acoustic_fails(self):
        for seconds in (math.nan, math.inf, -math.inf, -.1, True):
            self.assertEqual(self.verdict(self.result(seconds=seconds))["overall"], "fail")

    def test_file_ready_submission_digital_loopback_not_acoustic(self):
        for method in ("file_ready", "play_submit", "digital_loopback", "loopback_acoustic"):
            result = self.result(); result["acoustic"]["method"] = method
            self.assertEqual(self.verdict(result)["overall"], "fail")

    def test_placeholder_and_wrong_timing_boundary_fail(self):
        result = self.result(); result["answer_kind"] = "placeholder"
        self.assertEqual(self.verdict(result)["overall"], "fail")
        result = self.result(); result["acoustic"]["end_event"] = "play_submit"
        self.assertEqual(self.verdict(result)["overall"], "fail")

    def test_error_or_guess_zero_tolerance(self):
        for key, value in (("errors", ["false fact"]), ("guessed", True)):
            result = self.result(); result[key] = value
            self.assertEqual(self.verdict(result)["overall"], "fail")

    def test_knowledge_refusal_not_correct_unknown_refusal_can_be(self):
        result = self.result(); result["answer_kind"] = "refusal"
        self.assertEqual(self.verdict(result)["overall"], "fail")
        self.plan["tasks"][0]["kind"] = "uncertainty"
        self.assertEqual(self.verdict(result)["overall"], "pass")

    def test_missing_judgment_or_review_evidence_unmeasured(self):
        result = self.result(); del result["checks"]["facts"]
        self.assertEqual(self.verdict(result)["overall"], "unmeasured")
        result = self.result(); del result["checks"]["execution"]["evidence"]
        self.assertEqual(self.verdict(result)["overall"], "unmeasured")
        followup = copy.deepcopy(self.plan["tasks"][0]); followup.update(id="follow", kind="followup", prerequisite={"task_ids": ["zh-1"]})
        self.plan["tasks"].append(followup)
        row = self.round(); answer = self.result(mid="mic-follow"); answer["id"] = "follow"; row["results"].append(answer)
        self.assertEqual(evaluate(self.plan, [row])["overall"], "unmeasured")
        answer["context_evidence"] = "dialogue.json#actual-prior-turn"
        self.assertEqual(evaluate(self.plan, [row])["overall"], "pass")

    def test_fixed_plan_hash_and_round_order(self):
        row = self.round(); row["plan_sha256"] = "wrong"
        with self.assertRaises(ValueError): evaluate(self.plan, [row])
        row = self.round(index=1)
        with self.assertRaises(ValueError): evaluate(self.plan, [row])

    def test_initial_plus_two_improvements_and_no_more(self):
        rows = [self.round(self.result(mid="mic-"+str(i), seconds=2.1 if i < 2 else 1.5), i) for i in range(3)]
        report = evaluate(self.plan, rows)
        self.assertEqual(report["overall"], "pass")
        self.assertEqual([r["status"] for r in report["rounds"]], ["fail", "fail", "pass"])
        self.assertFalse(report["may_improve"])
        with self.assertRaises(ValueError): evaluate(self.plan, rows+[self.round(index=3)])

    def test_thermal_block_stops_and_does_not_fabricate_missing_result(self):
        row = self.round(); row["results"] = []
        row["blocker"] = {"kind": "thermal_limit", "reason": "stop limit", "evidence": "thermal.log#7", "observed_c": 70.1, "threshold_c": 70}
        report = evaluate(self.plan, [row])
        self.assertNotEqual(report["overall"], "pass")
        self.assertFalse(report["may_improve"])
        self.assertEqual(report["rounds"][0]["coverage"]["reported"], 0)
        with self.assertRaises(ValueError): evaluate(self.plan, [row, self.round(index=1)])

    def test_hardware_block_requires_explicit_per_item_block(self):
        row = self.round(); row["blocker"] = {"kind": "missing_hardware", "component": "measurement mic", "reason": "not present", "evidence": "inventory.txt"}
        result = row["results"][0]; result["status"] = "blocked"
        result["checks"] = {k: {"status": "blocked", "reason": "measurement fixture missing"} for k in CHECKS}
        result["acoustic"] = {"status": "blocked", "reason": "measurement fixture missing"}
        self.assertEqual(evaluate(self.plan, [row])["overall"], "blocked")
        row.pop("blocker")
        self.assertEqual(evaluate(self.plan, [row])["overall"], "fail")

    def test_duplicate_unknown_results_and_reused_capture_rejected(self):
        row = self.round(); row["results"] *= 2
        with self.assertRaises(ValueError): evaluate(self.plan, [row])
        row = self.round(); row["results"][0]["id"] = "not-planned"
        with self.assertRaises(ValueError): evaluate(self.plan, [row])
        report = evaluate(self.plan, [self.round(), self.round(index=1)])
        self.assertEqual(report["overall"], "fail")

    def test_empty_rounds_and_arbitrary_language_groups(self):
        self.assertEqual(evaluate(self.plan, [])["overall"], "unmeasured")
        self.plan["tasks"][0].update(language="ja", group="custom-group")
        self.assertEqual(self.verdict(self.result())["rounds"][0]["groups"], {"ja/custom-group": "pass"})
        result = self.result(); result["status"] = "unmeasured"
        self.assertEqual(self.verdict(result)["overall"], "unmeasured")


if __name__ == "__main__":
    unittest.main()
