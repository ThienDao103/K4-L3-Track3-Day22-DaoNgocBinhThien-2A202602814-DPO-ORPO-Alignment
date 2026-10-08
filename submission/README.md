# Bằng chứng nộp bài — Lab 22

Đào Ngọc Bình Thiên · 2A202602814 · K4 / Track 3. Phạm vi: phần bắt buộc NB0–NB4 trên T4.

## Đối chiếu rubric

| Yêu cầu | Bằng chứng |
|---|---|
| NB0: tự cài loss, khớp công thức và log(2) | `notebooks/00_dpo_loss_from_scratch.py`; output NB0 trong notebook đã chạy; `scripts/test_submission.py` kiểm tra trực tiếp hàm tự cài |
| NB0: likelihood displacement | REFLECTION §3, ví dụ số cả hai kịch bản |
| NB1: loss giảm, lưu SFT merge | `screenshots/02-sft-loss.png`; bảng loss và log merge thành công trong notebook; `adapters/sft-mini/adapter_config.json` |
| NB2: chia theo prompt, đọc ba cặp | `data/pref/train.parquet`, `eval.parquet`; assert/output ba cặp NB2; REFLECTION §1 |
| NB2: thiên vị độ dài | `data/pref/stats.json`; `screenshots/02b-pref-length.png`; 65,875% chosen dài hơn |
| NB3: reference là SFT | `adapters/dpo/adapter_config.json` trỏ `/content/lab22/models/sft-merged`; output train với `precompute_ref=True` |
| NB3: reward riêng train/held-out | `screenshots/03-dpo-reward-curves.png`; `adapters/dpo/dpo_metrics.json` |
| NB3: giải thích chẩn đoán | REFLECTION §3: chosen và rejected cùng tăng, điều kiện code gắn nhãn `INTENDED` |
| NB4: 8 câu cố định + ít nhất 50 held-out | `data/eval/side_by_side.jsonl`: 58 records; `SIDE_BY_SIDE.md`: toàn bộ 8 cặp cố định |
| NB4: judge, CI, sanity, kiểm soát độ dài | `data/eval/judge_summary.json`, `judge_results_rm.json`; REFLECTION §4 |
| Phản tư §3, §4, §6 | `REFLECTION.md`; §3 và §6 đều vượt yêu cầu độ dài |
| Tái lập | Bản sạch `colab/Lab22_DPO_T4.ipynb` và nguồn `notebooks/*.py`, `lab22/*.py`; bản giữ output riêng bên dưới |
| Verify | `scripts/verify.py` mã 0; transcript `verify.log`; giới hạn kiểm tra được mô tả bên dưới |

Notebook bằng chứng: [`colab/Lab22_DPO_T4_executed.ipynb`](../colab/Lab22_DPO_T4_executed.ipynb).
Không có cell error; các code cell bắt buộc đều có execution count và khớp nguồn tái lập.
`run_summary.json` ghi SHA-256, GPU, đồng hồ progress và thống kê đầu ra từ notebook/JSONL.
`data/eval/training_history.json` trích bảng log SFT và DPO held-out đã hiển thị, không tái tạo số liệu train DPO không có trong bảng.

## Kiểm tra và tái lập

Trên máy đã cài thư viện:

```bash
python -X utf8 scripts/verify.py
python -X utf8 -m pytest -q -p no:cacheprovider scripts/
python -X utf8 scripts/build_colab.py --check
```

Trên Linux/Colab có `make`, lệnh kiểm tra tương đương là `make verify` và `make test`.
Máy Windows hiện tại không có `make`, nên đã chạy Python trực tiếp.
Kết quả kiểm thử CPU: **60 passed**. Lỗi quyền thư mục tạm của sandbox trong lượt đầu được xử lý bằng lần chạy ngoài sandbox với thư mục tạm mới trong workspace, không thay đổi bài kiểm thử.

Để chạy lại huấn luyện, upload bản sạch `Lab22_DPO_T4.ipynb`, chọn T4 GPU và Run all.
Notebook tự ghi package `lab22` vào `/content/lab22`; không cần ZIP hay trọng số của lần chạy cũ.
Nếu dùng CLI, `make pipeline` thực thi NB0–NB4 và giữ output trong notebook riêng.
Các dependency của lab có khoảng phiên bản; bản đã chạy ghi Unsloth 2026.10.2, transformers 5.17.0,
torch 2.11.0+cu130 và PEFT 0.21.1. Seed cố định hỗ trợ tái lập nhưng không bảo đảm số liệu giống tuyệt đối trên mọi môi trường.

### Verify cho kết quả Colab đã xuất

Trọng số mô hình lớn và thư mục `models/` bị `.gitignore` loại khỏi bài nộp. Script verify gốc yêu cầu
`models/sft-merged/config.json` trên chính máy đang chạy và so đường dẫn tuyệt đối; yêu cầu này không phù hợp
với repo chỉ chứa bằng chứng xuất từ `/content/lab22` sang Windows.

Đã bổ sung `scripts/submission_evidence.py`: chỉ khi notebook đã chạy vượt kiểm tra nguồn code,
execution count, cell error, output lưu SFT merge, NB0/NB2/NB4 và đối chiếu metrics/summary với file xuất,
verify mới chấp nhận reference Colab `/content/lab22/models/sft-merged` và log merge thay cho config cục bộ.
Vẫn kiểm tra adapter config, fingerprint split, hash câu trả lời đã chấm, số held-out, ảnh và REFLECTION.
Các test kiểm tra trường hợp mất execution count, cell lỗi, sửa code hoặc metrics không khớp đều phải bị từ chối.
Nếu thiếu notebook hợp lệ, verify vẫn yêu cầu config SFT merge trên máy hiện tại như trước.

**Đây là kiểm tra bằng chứng bài nộp, không phải kiểm tra có thể inference trên Windows bằng trọng số đã tải.**
Không tạo config mô hình giả và không đổi đường dẫn trong adapter gốc.

## Tính toàn vẹn và trình bày

Notebook đã chạy và các JSON metrics, verdicts, JSONL câu trả lời, adapter config, Parquet được giữ nguyên
so với file upload. ZIP upload gốc vẫn giữ trên máy, không đưa vào Git vì đã tách các bằng chứng cần nộp.
Tokenizer JSON cũng chỉ giữ cục bộ, không cần commit để chấm báo cáo.

Ảnh `04-side-by-side-table.png` được dựng lại từ cùng 8 câu trả lời gốc để tránh chữ tràn/cắt;
ảnh xuất nguyên bản lưu ở `04-side-by-side-table-colab.png`, đồng thời vẫn nằm trong notebook đã chạy.
Chạy `python scripts/report_results.py` để dựng lại bảng và trích các log; script không train, không gọi mạng,
không thay câu trả lời hoặc metrics gốc. Các thẻ tool_call còn giữ trong cả ảnh và câu trả lời, được phân tích ở REFLECTION §4.

## Trạng thái nộp

Đã chuẩn bị đủ bằng chứng phần bắt buộc để đưa lên repo. Không yêu cầu điểm bonus vì các phần đó chưa chạy.
Theo rubric, chỉ file đã commit mới được tính: cần commit/push repo public và nộp URL vào LMS.
