import unittest

from companion_action_history import ActionHistory
from companion_models import ActionResult, Session


class ActionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.history = ActionHistory(clock=lambda: self.now)
        self.session = Session("retroarch", "RetroArch", 42, [], "/private/rom", "Game", None, [], {}, 0)

    def pending(self):
        return self.history.record(ActionResult(True, "save_state", "Save State", dispatch="steam_input", keys=["f2"]), self.session)

    def test_empty_journal(self):
        self.assertEqual(self.history.snapshot(), {"last_action": None, "action_history": []})

    def test_pending_then_sent_is_not_emulator_confirmation(self):
        response = self.pending()
        self.assertEqual(response["message"], "Save State")
        self.assertEqual(self.history.snapshot()["action_history"][0]["status"], "pending")
        self.assertTrue(self.history.report_keyboard(response["request_id"], True))
        report = self.history.snapshot()
        self.assertEqual(report["action_history"][0]["status"], "sent")
        self.assertIn("execution not confirmed", report["last_action"]["message"])
        self.assertTrue(report["last_action"]["ok"])
        self.assertNotIn("/private/rom", str(report))

    def test_failed_partial_dispatch_and_duplicate_report(self):
        response = self.pending()
        self.assertTrue(self.history.report_keyboard(response["request_id"], False, "key up failed"))
        self.assertFalse(self.history.report_keyboard(response["request_id"], True))
        report = self.history.snapshot()
        self.assertEqual(report["action_history"][0]["status"], "failed")
        self.assertIn("partial", report["last_action"]["message"])
        self.assertFalse(report["last_action"]["ok"])

    def test_unreported_keyboard_delivery_expires_without_retry_or_late_rewrite(self):
        response = self.pending()
        self.now = 15
        report = self.history.snapshot()
        self.assertEqual(report["action_history"][0]["status"], "unknown")
        self.assertIn("outcome unknown", report["last_action"]["message"])
        self.assertFalse(self.history.report_keyboard(response["request_id"], True))

    def test_old_reports_do_not_replace_newer_last_action(self):
        first, second = self.pending(), self.pending()
        self.assertTrue(self.history.report_keyboard(first["request_id"], False, "failure"))
        self.assertEqual(self.history.snapshot()["last_action"]["request_id"], second["request_id"])
        self.assertEqual(self.history.snapshot()["action_history"][0]["status"], "pending")

    def test_native_sent_local_completed_and_backend_failed(self):
        for result, status in (
            (ActionResult(True, "pause", "command sent, execution not confirmed", dispatch="retroarch_udp"), "sent"),
            (ActionResult(True, "slot_next", "Slot selected"), "completed"),
            (ActionResult(False, "save_state", "No active session"), "failed"),
        ):
            response = self.history.record(result, None)
            self.assertEqual(self.history.snapshot()["action_history"][0]["status"], status)
            self.assertFalse(self.history.report_keyboard(response["request_id"], True))

    def test_bounded_to_30_entries_and_evicted_ids_cannot_be_reported(self):
        first = self.pending()
        for _ in range(35):
            last = self.pending()
        snapshot = self.history.snapshot()
        self.assertEqual(len(snapshot["action_history"]), 30)
        self.assertEqual(snapshot["action_history"][0]["id"], last["request_id"])
        self.assertFalse(self.history.report_keyboard(first["request_id"], True))
        self.assertNotIn("_deadline", str(snapshot))

    def test_invalid_reports_do_not_mutate_pending_entry(self):
        response = self.pending()
        for request_id, delivered, error in ((None, True, ""), (response["request_id"], 1, ""),
                                              (response["request_id"], True, {}), ("unknown", False, "")):
            self.assertFalse(self.history.report_keyboard(request_id, delivered, error))
        self.assertEqual(self.history.snapshot()["action_history"][0]["status"], "pending")

    def test_snapshot_and_response_are_detached_and_messages_bounded(self):
        response = self.pending()
        response["keys"].append("x")
        snapshot = self.history.snapshot()
        snapshot["action_history"][0]["message"] = "changed"
        snapshot["last_action"]["keys"].append("y")
        self.assertEqual(self.history.snapshot()["last_action"]["keys"], ["f2"])
        self.assertNotEqual(self.history.snapshot()["action_history"][0]["message"], "changed")
        self.history.report_keyboard(response["request_id"], False, "x" * 10000)
        self.assertLessEqual(len(self.history.snapshot()["action_history"][0]["message"]), 400)


if __name__ == "__main__":
    unittest.main()
