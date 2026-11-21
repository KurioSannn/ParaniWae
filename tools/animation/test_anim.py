"""Tes generator & validator animasi (stdlib unittest). Jalankan: make animations-test"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import silat_anim as sa  # noqa: E402
import validate_anim as va  # noqa: E402

RIG = HERE / "rig.json"
MV = "mv.uji.kuda-kuda"


def spec(**over):
    s = {
        "schema": "silatara.keyframes/v1", "animation_id": "anim.uji.kuda-kuda.v1", "movement_id": MV, "animation_status": "generated",
        "title": "Uji", "description": "Uji", "view": "side", "source_ids": [],
        "keyframes": [
            {"id": "kf-1", "phase_id": f"{MV}#p1", "label": "Berdiri", "pose": {"pelvis": [172, 0], "feet": {"L": [176, 0], "R": [168, 0]}, "arms": {"L": [0, 0], "R": [0, 0]}}},
            {"id": "kf-2", "phase_id": f"{MV}#p2", "label": "Kuda-kuda", "pose": {"pelvis": [190, 14], "feet": {"L": [226, 0], "R": [128, 0]}, "arms": {"L": [0, 0], "R": [0, 0]}}},
        ],
        "sequence": [{"pose": "kf-1", "hold_ms": 800}, {"pose": "kf-2", "move_ms": 800, "hold_ms": 800}],
        "return_ms": 800,
    }  # fmt: skip
    s.update(over)
    return s


class AnimTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.d = self.tmp / MV
        self.d.mkdir()
        (self.d / "ANIMATION_NOTES.md").write_text("# catatan\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, s):
        (self.d / "keyframes.json").write_text(json.dumps(s))

    def test_build_produces_valid_looping_animation(self):
        self.write(spec())
        man = sa.build(self.d, RIG)
        self.assertEqual(man["movement_id"], MV)
        self.assertLess(man["max_ik_error_px"], sa.IK_TOLERANCE_PX)
        self.assertEqual(va.validate_dir(self.d, RIG, {f"{MV}#p1", f"{MV}#p2"}), [])
        svg = (self.d / "animation.svg").read_text()
        self.assertIn("animateTransform", svg)
        self.assertNotIn("<script", svg)

    def test_feet_stay_planted(self):
        rig = json.loads(RIG.read_text())
        frames, _, _ = sa.sample(rig, spec())
        ground = rig["canvas"]["ground_y"] - rig["segments"]["ankle_h"]
        for fr in frames:  # kedua kaki menapak di seluruh frame (lift = 0)
            self.assertAlmostEqual(fr.points["ankle.L"][1], ground, places=3)
            self.assertAlmostEqual(fr.points["ankle.R"][1], ground, places=3)

    def test_unreachable_pose_is_rejected(self):
        s = spec()
        s["keyframes"][1]["pose"]["feet"] = {"L": [330, 0], "R": [20, 0]}  # kaki terentang melebihi panjang tungkai
        self.write(s)
        with self.assertRaises(sa.AnimationError):
            sa.build(self.d, RIG)

    def test_missing_return_breaks_loop_and_is_rejected(self):
        self.write(spec(return_ms=0))
        with self.assertRaises(sa.AnimationError):
            sa.build(self.d, RIG)

    def test_external_reference_and_tampering_detected(self):
        self.write(spec())
        sa.build(self.d, RIG)
        p = self.d / "animation.svg"
        p.write_text(p.read_text().replace("<title", '<image href="https://example.com/x.png"/><title', 1))
        errs = va.validate_dir(self.d, RIG)
        self.assertTrue(any("eksternal" in e for e in errs), errs)
        self.assertTrue(any("berbeda dari manifest" in e for e in errs), errs)

    def test_stale_manifest_after_keyframe_edit(self):
        self.write(spec())
        sa.build(self.d, RIG)
        s = spec()
        s["title"] = "Diubah"
        self.write(s)
        self.assertTrue(any("kedaluwarsa" in e for e in va.validate_dir(self.d, RIG)))

    def test_phase_from_other_movement_rejected(self):
        s = spec()
        s["keyframes"][1]["phase_id"] = "mv.lain.gerak#p1"
        self.write(s)
        sa.build(self.d, RIG)
        self.assertTrue(any("bukan milik gerakan" in e for e in va.validate_dir(self.d, RIG)))

    def test_phase_missing_from_document_rejected(self):
        self.write(spec())
        sa.build(self.d, RIG)
        self.assertTrue(any("tidak ada di dokumen" in e for e in va.validate_dir(self.d, RIG, {f"{MV}#p1"})))

    def test_needs_reference_must_explain_and_have_no_svg(self):
        self.write({"animation_id": "anim.uji.kuda-kuda.v1", "movement_id": MV, "animation_status": "needs_reference", "title": "x"})
        self.assertTrue(any("needs" in e for e in va.validate_dir(self.d, RIG)))
        self.write({"animation_id": "anim.uji.kuda-kuda.v1", "movement_id": MV, "animation_status": "needs_reference", "title": "x", "needs": "foto berizin"})
        (self.d / "animation.svg").write_text("<svg/>")
        self.assertTrue(any("tidak boleh ada" in e for e in va.validate_dir(self.d, RIG)))

    def test_non_looping_values_detected(self):
        self.write(spec())
        sa.build(self.d, RIG)
        p = self.d / "animation.svg"
        txt = p.read_text()
        i = txt.index('type="rotate"')
        j = txt.index('values="', i) + len('values="')
        p.write_text(txt[:j] + "99;" + txt[j:])  # nilai awal != nilai akhir
        self.assertTrue(any("loop terputus" in e for e in va.validate_dir(self.d, RIG)))

    def test_top_view_diagram_and_text_clipping_check(self):
        s = {
            "animation_id": "anim.uji.kuda-kuda.v1", "movement_id": MV, "animation_status": "generated", "title": "Pola", "description": "d", "view": "top",
            "markers": [{"id": "kf-1", "phase_id": f"{MV}#p1", "label": "0", "pos": [180, 300]}, {"id": "kf-2", "phase_id": f"{MV}#p2", "label": "1", "pos": [180, 200]}],
            "guides": [{"type": "label", "at": [10, 100], "text": "teks yang terlalu panjang di tepi"}], "legend": "ok",
        }  # fmt: skip
        self.write(s)
        sa.build(self.d, RIG)
        self.assertTrue(any("terpotong" in e for e in va.validate_dir(self.d, RIG)))


class RepoAnimationsTest(unittest.TestCase):
    def test_all_repository_animations_valid(self):
        root = HERE.parent.parent / "content" / "pencak-silat" / "animations"
        if not root.is_dir():
            self.skipTest("folder animasi tidak ada")
        phases = va._phase_index(root.parent / "movements")
        bad = {d.name: va.validate_dir(d, RIG, phases) for d in root.iterdir() if d.is_dir()}
        self.assertEqual({k: v for k, v in bad.items() if v}, {})


if __name__ == "__main__":
    unittest.main()
