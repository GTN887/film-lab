#!/usr/bin/env python3
"""Pose Desk: still-first OpenPose-style guide, face lock, no puppeting claim."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from film_lab.hub import FORBIDDEN_BRANDS, HUB_CARDS
from film_lab.pose import (
    BODY_PRESETS,
    FACE_PRESETS,
    HAND_PRESETS,
    apply_pose_for_project,
    apply_pose_to_still,
    compose_keypoints,
    detect_pose_nodes,
    face_bbox_px,
    motion_step_html,
    pose_markdown,
    probe_pose,
    workflow_is_live,
    workflow_stub_note,
)
from film_lab.project import Project


FACE_PINK = (220, 40, 180)


def _still_with_face(path: Path) -> Path:
    img = Image.new("RGB", (400, 520), (22, 26, 32))
    for y in range(36, 148):
        for x in range(148, 252):
            img.putpixel((x, y), FACE_PINK)
    img.save(path)
    return path


class PoseDeskTests(unittest.TestCase):
    def test_presets_and_steps(self) -> None:
        bodies = [p.label for p in BODY_PRESETS]
        hands = [p.label for p in HAND_PRESETS]
        faces = [p.label for p in FACE_PRESETS]
        self.assertIn("Stand", bodies)
        self.assertIn("Kiss lean", bodies)
        self.assertIn("On chest", hands)
        self.assertIn("In hair", hands)
        self.assertIn("3/4", faces)
        self.assertIn("Profile", faces)
        keys = compose_keypoints("Kiss lean", "On chest", "3/4")
        self.assertIn("neck", keys)
        self.assertIn("r_wri", keys)
        steps = motion_step_html()
        self.assertIn("Upload", steps)
        self.assertIn("Pose adjust", steps)
        self.assertIn("Enhance", steps)
        self.assertIn("Animate", steps)
        md = pose_markdown().lower()
        self.assertIn("still-first", md)
        self.assertIn("not", md)
        self.assertIn("puppeting", md)
        self.assertIn("face", md)
        self.assertFalse(workflow_is_live())
        self.assertIn("8188", workflow_stub_note())

    def test_apply_keeps_face_pixels_and_writes_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = _still_with_face(Path(tmp) / "lead.png")
            dest = Path(tmp) / "posed.png"
            result = apply_pose_to_still(
                src, dest=dest, body="Lean in", hands="On chest", face="3/4"
            )
            self.assertTrue(result.path.is_file())
            self.assertTrue(result.json_path.is_file())
            self.assertTrue(result.face_preserved)
            self.assertEqual(result.method, "local_overlay")
            payload = json.loads(result.json_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["not_video_puppeting"])
            self.assertTrue(payload["still_first"])
            self.assertTrue(payload["face_preserved"])
            self.assertEqual(payload["body"], "Lean in")
            posed = Image.open(result.path).convert("RGB")
            inner = [
                posed.getpixel((x, y))
                for y in range(70, 110)
                for x in range(170, 230)
            ]
            self.assertTrue(all(px == FACE_PINK for px in inner), "face oval must stay original")
            x0, y0, x1, y1 = result.face_bbox
            self.assertLess(x0, 170)
            self.assertGreater(x1, 230)

    def test_project_ingest_and_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            project = Project.create("pose-study", data_root=root)
            src = _still_with_face(Path(tmp) / "ref.png")
            result = apply_pose_for_project(
                project, src, body="Stand", hands="Rest", face="Front"
            )
            self.assertTrue(result.path.is_file())
            self.assertEqual(result.path.parent, project.stills_dir)
            self.assertTrue(any(p.name.startswith("pose_") for p in project.list_stills()))
        status, msg = probe_pose()
        self.assertIn(status, {"Off", "Local", "Ready"})
        self.assertTrue(msg)
        found = detect_pose_nodes(
            {"OpenposePreprocessor": {}, "ControlNetApply": {}, "KSampler": {}}
        )
        self.assertEqual(found, ["OpenposePreprocessor", "ControlNetApply"])
        self.assertEqual(detect_pose_nodes({}), [])

    def test_hub_card_and_no_brands(self) -> None:
        titles = [c.title for c in HUB_CARDS]
        self.assertIn("Pose Desk", titles)
        self.assertEqual(len(HUB_CARDS), 15)
        pose = next(c for c in HUB_CARDS if c.tab_id == "pose")
        self.assertEqual(pose.index, "13")
        desk = next(c for c in HUB_CARDS if c.tab_id == "set")
        self.assertEqual(desk.title, "3D Set Desk")
        self.assertEqual(desk.index, "14")
        mark = next(c for c in HUB_CARDS if c.tab_id == "mark")
        self.assertEqual(mark.title, "Mark & Direct")
        self.assertEqual(mark.index, "15")
        self.assertIn("still", pose.blurb.lower())
        blob = pose_markdown() + motion_step_html() + workflow_stub_note()
        blob += " ".join(f"{p.label} {p.blurb}" for p in BODY_PRESETS + HAND_PRESETS + FACE_PRESETS)
        low = blob.lower()
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, low, banned)
        docs = (ROOT / "docs" / "POSE.md").read_text(encoding="utf-8").lower()
        self.assertIn("not frame-by-frame video puppeting", docs)
        self.assertIn("upload → pose adjust → enhance → animate", docs)
        for banned in FORBIDDEN_BRANDS:
            self.assertNotIn(banned, docs, banned)

    def test_bbox_helper(self) -> None:
        keys = compose_keypoints("Stand", "Rest", "Front")
        box = face_bbox_px(400, 520, keys)
        self.assertEqual(len(box), 4)
        self.assertLess(box[0], box[2])
        self.assertLess(box[1], box[3])


if __name__ == "__main__":
    unittest.main()
