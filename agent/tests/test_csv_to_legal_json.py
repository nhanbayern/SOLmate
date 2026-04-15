import json
import shutil
import unittest
from pathlib import Path

from app.ingestion.csv_to_legal_json import convert_csv_to_legal_json


class CsvToLegalJsonTest(unittest.TestCase):
    def test_convert_csv_to_legal_json_outputs_expected_structure(self) -> None:
        temp_path = Path("tests/_tmp_csv_to_legal_json")
        shutil.rmtree(temp_path, ignore_errors=True)
        temp_path.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(temp_path, ignore_errors=True))

        csv_path = temp_path / "sample_legal.csv"
        output_path = temp_path / "sample_legal.json"
        csv_path.write_text(
            "\n".join(
                [
                    '"MỘT SỐ QUY ĐỊNH VỀ ĐIỀU KIỆN VAY VỐN",,,',
                    ",Thông tư đang còn hiệu lực,,",
                    "Số Thông tư,Thông tư số 39/2016/TT-NHNN,,",
                    "Ngày ban hành ,12/30/2016,,",
                    "Ngày hiệu lực,3/15/2017,,",
                    'Tiêu đề Thông tư,"QUY ĐỊNH VỀ HOẠT ĐỘNG CHO VAY",,',
                    "Một số nội dung tại Thông tư như sau:,,,",
                    'Điều 4,"Nguyên tắc cho vay, vay vốn",,',
                    'khoản 1,"1. Hoạt động cho vay theo thỏa thuận.",,',
                    'khoản 2,"2. Khách hàng phải sử dụng vốn đúng mục đích.",,',
                    'Điều 7,Điều kiện vay vốn,,',
                    ',Tổ chức tín dụng xem xét cho vay khi khách hàng đủ điều kiện:,,',
                    'khoản 1,"1. Khách hàng có năng lực pháp luật dân sự.",,',
                    'Điểm a,"a) Có phương án sử dụng vốn khả thi.",,',
                    ',Bổ sung thông tin cho điểm a.,,',
                    '"Điều 8 (đã được sửa đổi, bổ sung tại khoản 2 điều 1 Thông tư 06/2023/TT-NHNN)",Những nhu cầu vốn không được cho vay,,',
                    ',Tổ chức tín dụng không được cho vay đối với các nhu cầu vốn:,,',
                    'Điều 10 quy định loại cho vay như sau:,"1. Cho vay ngắn hạn.",,',
                    ',2. Cho vay trung hạn.,,',
                ]
            ),
            encoding="utf-8",
        )

        total_articles, _ = convert_csv_to_legal_json(csv_path, output_path)

        self.assertEqual(total_articles, 7)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["document_id"], "39/2016/TT-NHNN")
        self.assertEqual(payload["document_type"], "Thông tư")
        self.assertTrue(payload["is_active"])
        self.assertEqual(payload["issue_date"], "2016-12-30")
        self.assertEqual(payload["effective_date"], "2017-03-15")

        self.assertEqual(
            payload["articles"][0],
            {
                "article": "Điều 4",
                "article_content": "Nguyên tắc cho vay, vay vốn",
                "clause": "Khoản 1",
                "clause_content": "Hoạt động cho vay theo thỏa thuận.",
                "point": None,
                "point_content": None,
                "section_path": ["Điều 4, Khoản 1"],
            },
        )
        self.assertEqual(payload["articles"][2]["section_path"], ["Điều 7"])
        self.assertEqual(
            payload["articles"][2]["clause_content"],
            "Tổ chức tín dụng xem xét cho vay khi khách hàng đủ điều kiện:",
        )
        self.assertEqual(payload["articles"][4]["point"], "Điểm a")
        self.assertEqual(
            payload["articles"][4]["point_content"],
            "Có phương án sử dụng vốn khả thi.\nBổ sung thông tin cho điểm a.",
        )
        self.assertEqual(
            payload["articles"][5]["article"],
            "Điều 8 (đã được sửa đổi, bổ sung tại khoản 2 điều 1 Thông tư 06/2023/TT-NHNN)",
        )
        self.assertEqual(
            payload["articles"][5]["section_path"],
            ["Điều 8 (đã được sửa đổi, bổ sung tại khoản 2 điều 1 Thông tư 06/2023/TT-NHNN)"],
        )
        self.assertEqual(payload["articles"][6]["article"], "Điều 10")
        self.assertEqual(
            payload["articles"][6]["clause_content"],
            "1. Cho vay ngắn hạn.\n2. Cho vay trung hạn.",
        )


if __name__ == "__main__":
    unittest.main()
