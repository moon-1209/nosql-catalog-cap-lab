# Báo cáo kiểm kê dataset giọng nói

## 1. Thống kê số file theo nhóm thư mục

### data/raw/real_voice
- Tổng số file: 393

### src/data/stt/processed/real_voice
- Tổng số file: 393

### src/data/stt/finetuning/datasets
- Tổng số file: 6

## 2. Cấu trúc thư mục nguồn
```text
data/raw/real_voice
data/raw/real_voice/Female 30
data/raw/real_voice/Hoàng Tuấn
data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi
data/raw/real_voice/Male 30
data/raw/real_voice/Phương Uyên
data/raw/real_voice/Phương Uyên/Giọng clone
data/raw/real_voice/Phương Uyên/Nữ 20 tuổi
data/raw/real_voice/Phương Uyên/Trẻ con
data/raw/real_voice/Phương Uyên/Trẻ con/Nam 10
data/raw/real_voice/Phương Uyên/Trẻ con/Nữ 10
```

## 3. Danh sách file âm thanh nguồn
```text
```

## 4. Danh sách file âm thanh đã xử lý
```text
```

## 5. Thống kê nhóm giọng trong manifest
```text
--- src/data/stt/finetuning/datasets/pending_review/metadata.csv
sample_id,audio_path,raw_path,speaker_id,prompt_group,proposed_split,mode,intent,script_reference,model_prediction,transcript_verified,verification_status,reviewer_notes,verification_timestamp,duplicate_of,annotation_source
A_01_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_01_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_01_r.m4a,A
A_02_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_02_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_02_r.m4a,A
A_03_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_03_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_03_r.m4a,A
A_04_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_04_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_04_r.m4a,A
A_05_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_05_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_05_r.m4a,A
A_06_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_06_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_06_r.m4a,A
A_07_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_07_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_07_r.m4a,A
A_08_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_08_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_08_r.m4a,A
A_09_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_09_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_09_r.m4a,A
A_10_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_10_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_10_r.m4a,A
A_11_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_11_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_11_r.m4a,A
A_12_r,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_12_r.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_12_r.m4a,A
Số dòng dữ liệu:
--- src/data/stt/finetuning/datasets/pending_transcripts/metadata.csv
sample_id,audio_path,raw_path,speaker_id,prompt_group,mode,intent,script_reference,model_prediction,verbatim_transcript,transcript_status,reviewer_notes,verification_timestamp,duplicate_of,annotation_source
A_01_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_01_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_01_n.m4a,A
A_02_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_02_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_02_n.m4a,A
A_03_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_03_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_03_n.m4a,A
A_04_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_04_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_04_n.m4a,A
A_05_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_05_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_05_n.m4a,A
A_06_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_06_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_06_n.m4a,A
A_07_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_07_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_07_n.m4a,A
A_08_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_08_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_08_n.m4a,A
A_09_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_09_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_09_n.m4a,A
A_10_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_10_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_10_n.m4a,A
A_11_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_11_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_11_n.m4a,A
A_12_n,src/data/stt/processed/real_voice/wav/Hoàng Tuấn/Nam 20 tuổi/A_12_n.wav,data/raw/real_voice/Hoàng Tuấn/Nam 20 tuổi/A_12_n.m4a,A
Số dòng dữ liệu:
--- src/data/stt/finetuning/datasets/train/metadata.csv
sample_id,audio_path,raw_path,speaker_id,prompt_group,mode,intent,transcript,transcript_source,verification_status,human_verified,split,annotation_source
Số dòng dữ liệu:
--- src/data/stt/finetuning/datasets/validation/metadata.csv
sample_id,audio_path,raw_path,speaker_id,prompt_group,mode,intent,transcript,transcript_source,verification_status,human_verified,split,annotation_source
Số dòng dữ liệu:
--- src/data/stt/finetuning/datasets/test/metadata.csv
sample_id,audio_path,raw_path,speaker_id,prompt_group,mode,intent,transcript,transcript_source,verification_status,human_verified,split,annotation_source
Số dòng dữ liệu:
--- src/data/stt/finetuning/datasets/excluded/metadata.csv
sample_id,audio_path,raw_path,speaker_id,prompt_group,mode,intent,script_reference,excluded_reason,duplicate_of,annotation_source
Nu_C01,src/data/stt/processed/real_voice/wav/Nu_C01.wav,data/raw/real_voice/Nu_C01.m4a,B
Nu_C02,src/data/stt/processed/real_voice/wav/Nu_C02.wav,data/raw/real_voice/Nu_C02.m4a,B
Nu_C03,src/data/stt/processed/real_voice/wav/Nu_C03.wav,data/raw/real_voice/Nu_C03.m4a,B
Nu_C04,src/data/stt/processed/real_voice/wav/Nu_C04.wav,data/raw/real_voice/Nu_C04.m4a,B
Nu_C05,src/data/stt/processed/real_voice/wav/Nu_C05.wav,data/raw/real_voice/Nu_C05.m4a,B
Nu_C06,src/data/stt/processed/real_voice/wav/Nu_C06.wav,data/raw/real_voice/Nu_C06.m4a,B
Nu_C07,src/data/stt/processed/real_voice/wav/Nu_C07.wav,data/raw/real_voice/Nu_C07.m4a,B
Nu_C08,src/data/stt/processed/real_voice/wav/Nu_C08.wav,data/raw/real_voice/Nu_C08.m4a,B
Nu_C09,src/data/stt/processed/real_voice/wav/Nu_C09.wav,data/raw/real_voice/Nu_C09.m4a,B
Nu_C10,src/data/stt/processed/real_voice/wav/Nu_C10.wav,data/raw/real_voice/Nu_C10.m4a,B
Số dòng dữ liệu:
```
