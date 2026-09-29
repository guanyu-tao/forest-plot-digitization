"""Small synthetic cases for data-preserving pipeline invariants."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import forest_plot as fp
import export_xlsx as ex
from openpyxl import load_workbook


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        self.work.mkdir()
        self.output = self.root / "output"
        self.output.mkdir()
        self.pdf = self.root / "synthetic.pdf"
        self.pdf.write_bytes(b"synthetic fixture; never a real scan")
        fp.jwrite(self.work / "inventory.json", {"pdfs": [{"name": self.pdf.name, "stem": self.pdf.stem, "path": str(self.pdf), "pages": 1, "sha256": fp.digest(self.pdf)}]})
        fp.jwrite(self.work / "page_reviews.json", {self.pdf.name: {"1": {"expected_rows": 2, "checked": True, "xy_unit": "cm", "unit_evidence": "synthetic page heading"}}})
        fp.jwrite(fp.ocr_path(self.work, self.pdf.stem, 1), {"tokens": [{"text": "=1+1", "score": 0.8, "poly": [[0, 0], [1, 0], [1, 1], [0, 1]]}]})

    def record(self, row, tag, x, species="尖连蕊茶"):
        return {"pdf": self.pdf.name, "page": 1, "row": row, "checked": True, "sample": "0304", "small": 2, "tag": tag, "species": species, "x": x, "y": 300, "dbh": 2.5, "d1": "1.2g", "d2": None, "d3": None, "d4": None, "d5": None, "d6": None, "remark": "枯立；已采", "date": "2026-09-01"}

    def test_finalize_export_validate_and_literal_ocr(self):
        rows = [self.record(1, "HHBX03040001", 250), self.record(2, "HHBX03040001", 600)]
        fp.write_jsonl(self.work / "reviewed.jsonl", rows)
        fp.finalize(SimpleNamespace(workdir=str(self.work), profile=str(fp.DEFAULT_PROFILE)))
        payload = fp.jread(self.work / "final_payload.json")
        output = payload["outputs"][0]
        self.assertEqual(output["record_count"], 2)
        self.assertEqual(output["pending_count"], 2)  # duplicate tag, plus x out of range
        self.assertEqual(output["main"][0][7], "尖连蕊茶")  # alias is only a suggestion
        self.assertEqual(output["main"][0][8], 2.5)
        self.assertEqual(output["main"][1][8], 6.0)
        self.assertEqual(output["main"][0][12], "g")  # no invented suffix number
        self.assertEqual(output["main"][0][23], "枯立")
        ex.export_one(payload, output, self.output, False, 1)
        fp.validate(SimpleNamespace(workdir=str(self.work), output_dir=str(self.output)))
        book = load_workbook(self.output / output["file_name"])
        self.assertEqual(book.sheetnames, ["主表", "原始OCR", "质检汇总", "修订记录"])
        self.assertEqual(book["原始OCR"]["D2"].value, "=1+1")
        self.assertEqual(book["原始OCR"]["D2"].data_type, "s")
        with self.assertRaises(FileExistsError):
            ex.export_one(payload, output, self.output, False, 1)

    def test_out_of_range_page_rejected(self):
        rows = [self.record(1, "HHBX03040001", 250), self.record(2, "HHBX03040002", 300)]
        rows[1]["page"] = 2
        fp.write_jsonl(self.work / "reviewed.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "页码范围外"):
            fp.finalize(SimpleNamespace(workdir=str(self.work), profile=str(fp.DEFAULT_PROFILE)))


if __name__ == "__main__":
    unittest.main()
