# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

import torch
import librosa
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

model_id = "Qualcomm-AI-Research/PhoASR-whisper-small"
device = "cuda" if torch.cuda.is_available() else "cpu"

model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id).to(device)
processor = AutoProcessor.from_pretrained(model_id)


def transcribe(audio_path, language="vi"):
    sr = processor.feature_extractor.sampling_rate
    audio, _ = librosa.load(audio_path, sr=sr)

    inputs = processor(
        audio, sampling_rate=sr, return_tensors="pt", return_attention_mask=True
    )
    
    input_features = inputs.input_features.to(device)
    attention_mask = inputs.attention_mask.to(device)

    num_frames = int(attention_mask.sum().item())

    outputs = model.generate(
        input_features=input_features,
        attention_mask=attention_mask,       # used by transformers >= 4.54
        num_frames=num_frames,               # used by transformers <= 4.53
        language=language,
        task="transcribe",
        return_timestamps="word",            # the string, NOT True or False
        return_token_timestamps=True,
        return_dict_in_generate=True,
    )

    text = processor.batch_decode(outputs["sequences"], skip_special_tokens=True)[0]

    token_timestamps = torch.cat(
        [seg["token_timestamps"] for seg in outputs["segments"][0]]
    ).unsqueeze(0)

    model_outputs = [{
        "tokens": outputs["sequences"],
        "token_timestamps": token_timestamps,
        "stride": (audio.shape[0] / sr, 0.0, 0.0),
    }]
    
    time_precision = processor.feature_extractor.chunk_length / model.config.max_source_positions

    _, optional = processor.tokenizer._decode_asr(
        model_outputs, return_timestamps="word", return_language=False,
        time_precision=time_precision,
    )
    
    return text.strip(), optional["chunks"]


if __name__ == "__main__":
    text, chunks = transcribe("path-to-audio-sample")
    print("# Full Text:")
    print(text)
    print("# Word-level Timestamps:")
    print(chunks)
 