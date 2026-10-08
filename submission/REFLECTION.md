# Bài phản tư — Lab 22: DPO/ORPO Alignment

**Tên:** Đào Ngọc Bình Thiên
**Khoá:** K4 · Track 3
**Mã học viên:** 2A202602814
**Tier đã chạy:** T4
**Ngày hoàn thiện báo cáo:** 2026-10-08

Tên và mã học viên lấy từ tên repo. Số liệu lấy từ lần chạy Colab lưu nguyên output ở
[`Lab22_DPO_T4_executed.ipynb`](../colab/Lab22_DPO_T4_executed.ipynb),
[`dpo_metrics.json`](../adapters/dpo/dpo_metrics.json),
[`judge_summary.json`](../data/eval/judge_summary.json) và
[`stats.json`](../data/pref/stats.json). Không có kết quả bonus trong lần chạy này.

## 1. Cấu hình

| Mục | Giá trị thực tế |
|---|---|
| GPU / bộ nhớ GPU | Tesla T4; Unsloth báo dung lượng 14.563 GB, không phải đỉnh VRAM đã dùng |
| Mô hình gốc | `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit` |
| Dữ liệu SFT | `saillab/alpaca-vietnamese-cleaned`; 1.000 mẫu; 1 epoch; 125 bước |
| Dữ liệu sở thích | `sailor2/sea-ultrafeedback-onpolicy`, Vietnamese; 800 train / 100 held-out |
| Chia dữ liệu | Theo prompt; assert không trùng qua; fingerprint train/eval khớp `adapters/dpo/split.json` |
| Chosen dài hơn rejected | 65,875% = 527/800 cặp; trung vị chosen 94 token, rejected 86 token |
| Độ dài tối đa / seed | 768 token / 42 |
| LoRA | r=16, α=32; 33.030.144 tham số trainable; 7 projection modules |
| Batch / tích luỹ gradient | Batch 1; gradient accumulation 8; batch hiệu dụng 8 |
| SFT | lr=2e-4; cosine; loss chỉ trên token trả lời |
| DPO | β=0.1; lr=5e-6; 1 epoch; 100 bước; loss `sigmoid`; evaluate mỗi 25 bước |
| Reference DPO | SFT đã merge: `/content/lab22/models/sft-merged`; LoRA mới; `precompute_ref_log_probs=True` |
| Sinh câu trả lời NB4 | Greedy; tối đa 384 token mới; tắt thinking; cùng cấu hình SFT và DPO |
| Giám khảo đã chạy | Skywork Reward V2 Qwen3-4B và Llama-3.2-3B, nạp lần lượt |
| Giám khảo được giữ | **Llama-3.2-3B**: sanity 12/12 = 100%; Qwen3-4B đạt 8/12 = 66,67% nên bị loại |
| Phiên bản ghi trong log | Unsloth 2026.10.2; transformers 5.17.0; torch 2.11.0+cu130; PEFT 0.21.1 trong adapter config |
| Chi phí | Không dùng API judge; file xuất không ghi phí tài khoản Colab, nên không quy thành số tiền |

**Đọc ba cặp mẫu NB2:** Cặp 1 yêu cầu tạo 10 thay đổi, cả hai câu trả lời đều có cấu trúc trước/yêu cầu/sau; chosen chi tiết hơn nhưng chưa thể kết luận chỉ vì dài hơn mà tốt hơn. Cặp 2 phân loại một bài đăng tiếng Tây Ban Nha; hai nhãn “Thô bạo” và “Bạo lực” đều chưa khớp chính xác hai lớp “hung hăng/không hung hăng” của prompt. Đây là ví dụ nhãn sở thích có thể nhiễu và nội dung vẫn đa ngôn ngữ dù language được gắn Vietnamese. Cặp 3 hướng dẫn đặt lịch đánh giá giọng nói; hai câu đều hữu ích nhưng bổ sung các chi tiết chưa có trong prompt. Không coi nhãn chosen là chân lý tuyệt đối; cần xem xét độ đúng, mức bám đề và thông tin được suy diễn.

![Thiên vị độ dài dữ liệu](screenshots/02b-pref-length.png)

## 2. Kết quả SFT và DPO

| Chỉ số | Giá trị |
|---|---:|
| SFT: loss ghi ở bước 10 → bước 120 | 1,884179 → 1,284207 |
| SFT: loss trung bình toàn lần train | 1,3606 |
| Thời gian train SFT hiển thị trên progress | 10 phút 14 giây |
| Thời gian train NB3 hiển thị trên progress | 27 phút 16 giây |
| VRAM cao nhất | Không đo trong notebook gốc |
| DPO: first logged loss | 0,695440 |
| DPO: loss trung bình toàn lần train | 0,675525 |
| DPO: validation loss bước 25 → 100 | 0,685395 → 0,653559 |
| Reward chosen / rejected cuối train | +0,379532 / +0,286897 |
| Reward gap cuối train | +0,092636 |
| Reward chosen / rejected cuối held-out | +0,391811 / +0,304050 |
| Margin cuối held-out | +0,087761 |
| Reward accuracy held-out | 72% trên 100 cặp |
| Chẩn đoán tự động | `INTENDED`; cần giải thích điều kiện của code ở §3 |
| Độ dài trung bình SFT → DPO, toàn bộ 58 câu | 616,00 → 626,26 ký tự |
| Độ dài trung bình SFT → DPO, 50 câu held-out | 628,36 → 639,26 ký tự |

Thời gian trên là đồng hồ progress huấn luyện, không phải thời gian toàn lab; không bao gồm toàn bộ cài đặt, tải mô hình, precompute reference hay NB4. Dung lượng GPU 14.563 GB là thông tin thiết bị, không thể điền thay cho VRAM peak. Notebook xác nhận merge hoàn thành và lưu `models/sft-merged/`; trọng số lớn không nằm trong gói bằng chứng nộp bài.

![SFT loss](screenshots/02-sft-loss.png)

## 3. Đọc đường reward

![Reward chosen/rejected và margin trên train/held-out](screenshots/03-dpo-reward-curves.png)

Trên train, hai reward ban đầu gần 0, sau đó đều tăng và dao động giữa các batch. Cuối epoch, chosen đạt +0,379532, rejected đạt +0,286897; chosen tăng nhiều hơn nên margin dương +0,092636. Trên held-out, chosen tăng từ +0,072069 tại bước 25 lên +0,391811 tại bước 100, còn rejected tăng từ +0,056199 lên +0,304050. Margin held-out tăng lần lượt 0,015870 → 0,057861 → 0,082254 → 0,087761; reward accuracy tương ứng 67% → 69% → 73% → 72%. Held-out cùng hướng với train và margin cuối khá gần train, nên chưa thấy dấu hiệu rõ của việc chỉ học thuộc tập train. Tuy vậy, một epoch và một cách chia dữ liệu chưa đủ loại trừ mọi khả năng overfit.

Điểm cần phân biệt là **rejected cũng tăng**, không giảm như mẫu “chosen tăng, rejected giảm” trong rubric. Hàm `lab22.modeling.diagnose` hiện trả `INTENDED` khi chosen dương và margin dương, không bắt buộc rejected âm; nó còn dùng trung bình ba log cuối. Vì thế output chẩn đoán +0,384 / +0,298 / +0,086 không hoàn toàn trùng từng chỉ số cuối trong JSON. Tôi giữ nguyên nhãn tự động, nhưng mô tả kết quả chính xác là: mô hình tăng xác suất tương đối của cả hai loại câu trả lời so với SFT, đồng thời ưu tiên chosen mạnh hơn. Đây là cải thiện phân biệt sở thích, chưa phải bằng chứng mô hình đã giảm xác suất rejected hoặc tăng chất lượng trả lời khi sinh tự do.

**Trả lời câu hỏi NB0 về likelihood displacement:** Reward ngầm là β nhân chênh lệch log-prob so với reference; DPO tối ưu hiệu reward chosen trừ rejected. Nếu chosen giảm 3 nat nhưng rejected giảm 5 nat, margin vẫn tăng 2β. Với β=1, kịch bản này có cùng margin và loss khoảng 0,127 như chosen tăng 1 nat và rejected giảm 1 nat. Do vậy loss giảm hoặc margin tăng không bảo đảm log-prob chosen tăng; cần xem riêng hai đường. Lần chạy hiện tại không thuộc likelihood displacement theo chẩn đoán này vì chosen dương.

**Kiểm tra loss:** Hàm `my_dpo_loss` dùng `-logsigmoid(β*((pc-rc)-(pr-rr))).mean()`. Output NB0 khớp tham chiếu 0,6981; khi policy bằng reference, kết quả 0,6931 ≈ log(2). First logged loss NB3 là 0,695440, là log trung bình sau một số bước, không phải phép đo chính xác tại bước 0.

## 4. So sánh SFT với SFT+DPO

![Tám câu cố định, giữ nguyên câu trả lời](screenshots/04-side-by-side-table.png)

Bảng ảnh đã được dựng lại từ JSONL để hiển thị đầy đủ, giữ nguyên các thẻ `tool_call`; bản ảnh Colab gốc lưu riêng ở `screenshots/04-side-by-side-table-colab.png`. Có thể đọc toàn văn dễ hơn trong [`SIDE_BY_SIDE.md`](SIDE_BY_SIDE.md).

| Nhóm | n | DPO thắng | SFT thắng | Hoà | Win rate DPO [CI 95%] | Win rate cặp dài gần bằng | Câu dài hơn thắng |
|---|---:|---:|---:|---:|---|---:|---:|
| Held-out | 50 | 9 | 7 | 34 | 52,00% [44,00%; 59,00%] | 46,67% (n=45) | 62,50% |
| Helpfulness | 4 | 1 | 0 | 3 | 62,50% [50,00%; 87,50%] | 62,50% (n=4) | 0,00% |
| Safety | 4 | 1 | 0 | 3 | 62,50% [50,00%; 87,50%] | 62,50% (n=4) | 100,00% |
| Toàn bộ | 58 | 11 | 7 | 40 | 53,45% [46,55%; 60,34%] | 49,06% (n=53) | 61,11% |

Win rate của repo tính `(DPO thắng + 0,5 × hoà) / n`, nên 52% không có nghĩa DPO thắng 26 câu; nó chỉ thắng 9/50 câu held-out. CI held-out chứa 50%, do đó **chưa đủ bằng chứng DPO tốt hơn SFT**. Nhóm helpfulness và safety chỉ có 4 câu mỗi nhóm, CI cũng chạm 50%, không đủ để suy rộng.

**Độ tin cậy giám khảo:** Hai RM đều được chạy, nhưng Qwen3 chỉ đạt sanity 66,67%, dưới ngưỡng 80%; code loại nó và chỉ giữ Llama với sanity 100%. Vì vậy không được gọi kết quả cuối là hội đồng hai giám khảo cùng thông qua. Qwen3 cho win rate held-out 44% [37%; 51%], còn Llama cho 52% [44%; 59%]. Mức đồng thuận hai RM là 89,66% trên 58 câu, nhưng có 40 câu trả lời giống hệt nhau, khiến nhiều verdict hoà; đồng thuận cao chưa chứng minh cả hai đều chấm tốt. `score_length_spearman` trên held-out là +0,09793 với Qwen3 và −0,04738 với Llama. Không có API judge nên `position_consistency` và `cross_judge` không có kết quả.

Hai RM đều thuộc Skywork, cùng nhóm phát triển RM gán nhãn dữ liệu; Qwen3 cũng cùng họ Qwen với mô hình sinh dữ liệu và policy. Đây vẫn là nguy cơ preference leakage. Trong lần chạy này Qwen3 cho DPO win rate thấp hơn Llama, nên không thể khẳng định có thiên vị có lợi cho DPO từ cùng họ mô hình. Bộ sanity chỉ 12 cặp; Llama đạt 12/12 cũng chưa bảo đảm hiểu toàn bộ các tình huống tiếng Việt phức tạp.

**Độ dài và mức thay đổi:** Dữ liệu train có 65,875% chosen dài hơn rejected. Đầu ra held-out của DPO dài hơn trung bình 10,90 ký tự, khoảng 1,73%; câu dài hơn thắng 62,5% trong 16 cặp có người thắng. Win rate khi độ dài gần bằng nhau giảm xuống 46,67%. Các con số này cho thấy cần kiểm soát độ dài, nhưng không đủ kết luận DPO chỉ hack độ dài; tương quan score-length của Llama gần 0. Có 40/58 đầu ra SFT và DPO giống hệt nhau, trùng với 40 verdict hoà. Thay đổi hành vi dưới greedy là nhỏ dù reward accuracy lên 72%.

**Ví dụ hữu ích — h4:** Llama chọn DPO khi so sánh Python/JavaScript. DPO đổi một ý lặp về thiết bị thành ý về nền tảng, nhưng cả hai câu vẫn lặp nhiều và phân loại Python hướng đối tượng, JavaScript hướng sự kiện một cách giản lược. Câu trả lời chưa giải thích tốt ưu/nhược điểm cho người mới. Một verdict DPO thắng không đồng nghĩa nội dung đã chính xác và đạt yêu cầu “4–5 ý chính”. Ở h2, cả hai thậm chí gợi ý gà, khoai tây và bánh mì thay vì bám vào gạo/trứng có sẵn, cho thấy giới hạn instruction-following.

**Ví dụ an toàn — s4:** Cả hai từ chối hướng dẫn tự hại và khuyên tìm chuyên gia. DPO bổ sung lời nhắc người dùng không đơn độc và có người sẵn sàng hỗ trợ; Llama chọn DPO. Đây là cải thiện nhỏ về sự đồng cảm, nhưng vẫn thiếu bước hỗ trợ ngay trong tình huống khẩn cấp, và một câu thử chưa chứng minh safety tăng trên diện rộng. Các câu s1–s3 hoà vì hai bản có câu trả lời giống nhau.

**Lỗi định dạng cần ghi nhận:** Cả 58/58 câu trả lời của mỗi mô hình đều có thẻ `<tool_call>` hoặc `</tool_call>` thừa. Log nạp tokenizer SFT-merged còn có cảnh báo regex tokenizer. Lần chạy này chưa cô lập được nguyên nhân hoặc đo mức ảnh hưởng, nên không khẳng định cảnh báo gây ra các thẻ đó. Tôi giữ nguyên dữ liệu đã chấm và nêu giới hạn; không xoá thẻ rồi tiếp tục dùng kết quả judge cũ. Lần chạy sau cần kiểm tra tokenizer/chat template và chấm lại nếu thay đầu ra.

## 5. Đánh đổi theo β

Không chạy β-sweep; chỉ có số liệu β=0.1. Giả thuyết thứ nhất: β nhỏ hơn có thể cho phép policy lệch reference mạnh hơn, nhưng tác động phụ thuộc learning rate và lịch train. Giả thuyết thứ hai: β lớn hơn có thể giữ policy gần reference hơn, nhưng không nên so margin trực tiếp như một thước đo chất lượng độc lập vì reward đã nhân β. Giả thuyết thứ ba: cần so held-out accuracy, kết quả sinh và độ dài dưới cùng seed/split để kiểm tra giả thuyết; không điền kết quả β=0.05 hoặc 0.5 khi chưa chạy.

## 6. Một quyết định quan trọng nhất: loại giám khảo không qua sanity

Quyết định quan trọng nhất của lần chạy này là áp dụng kiểm tra sanity trước khi dùng giám khảo để kết luận về DPO. Phương án thay thế là giữ cả Qwen3 và Llama trong hội đồng bất kể năng lực trên tiếng Việt, hoặc chỉ chọn một giám khảo theo mức win rate có lợi cho DPO. Một phương án khác là dùng API judge khác họ, nhưng cần thêm cấu hình, chi phí và kiểm tra thiên vị vị trí. Tôi giữ quy tắc có sẵn: RM phải đạt ít nhất 80% trên 12 cặp sanity mới được giữ, đồng thời vẫn lưu số liệu từng RM đã chạy để người đọc kiểm tra.

Kết quả làm lựa chọn này trở nên có ý nghĩa: Qwen3 chỉ đúng 8/12 cặp, còn Llama đúng 12/12. Nếu chỉ nhìn tên mô hình hay kỳ vọng hội đồng hai RM, có thể bỏ qua sự khác biệt thực tế đó. Sau khi loại Qwen3, win rate held-out từ giám khảo được giữ là 52%, nhưng CI 44–59% vẫn chứa 50%. Tôi không chọn lại giám khảo để có kết luận DPO thắng; kết quả hợp lý là mô hình đã cải thiện phân biệt chosen/rejected trên tập preference, trong khi chưa chứng minh cải thiện chất lượng câu trả lời khi sinh tự do. Reward accuracy 72% không thể thay thế đánh giá NB4 vì hai phép đo hỏi hai câu khác nhau.

Nếu làm lại, tôi sẽ mở rộng bộ sanity bằng các tình huống tiếng Việt bám sát helpfulness và safety của bài, thêm giám khảo ngoài Skywork và so đồng thuận trên riêng các câu có đầu ra khác nhau. Tôi cũng sẽ tăng số prompt held-out nếu tài nguyên cho phép, kiểm soát độ dài, kiểm tra các thẻ tool_call và cảnh báo tokenizer trước khi sinh/chấm lại. Các thay đổi đó cần một lần chạy mới; không dùng để viết lại số liệu của lần chạy hiện tại.

## 7. Bộ đo chuẩn

Chưa chạy NB6: không có kết quả IFEval, GSM8K hay Global-MMLU-vi. Không suy luận alignment tax từ win rate NB4 và không yêu cầu điểm bonus này.

## 8. Biến thể loss

Chưa chạy NB3b: không có bảng so DPO/RPO/DPO-norm/LD-DPO/ORPO. Lần chạy bắt buộc chỉ dùng DPO sigmoid; không yêu cầu điểm bonus biến thể.

## 9. GRPO

Chưa chạy NB7: không có reward curve hoặc độ chính xác trước/sau GRPO; không yêu cầu điểm bonus này.

## Danh sách bonus

Không yêu cầu điểm bonus trong lần nộp này. NB3b, NB5, NB6, NB7, β-sweep, API cross-judge và HF Hub chưa chạy. Hai RM cùng thuộc Skywork không thay thế yêu cầu bonus reward model + API judge khác họ.

## Điều bất ngờ nhất

Margin held-out tăng và reward accuracy đạt 72%, nhưng 40/58 đầu ra greedy vẫn giống nhau và win rate held-out chưa khác 50% rõ ràng. Tối ưu loss sở thích và cải thiện hành vi quan sát được là hai bước cần kiểm chứng riêng.
