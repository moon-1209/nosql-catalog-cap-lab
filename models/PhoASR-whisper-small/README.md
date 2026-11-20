---
license:
- bsd-3-clause-clear
- other
license_name: qualcomm-responsible-ai-license
license_link: >-
  https://www.qualcomm.com/site/responsible-ai-license
language:
- vi
---

# PhoASR-whisper-small: Vietnamese Automatic Speech Recognition - A Revisit

> We introduce `PhoASR-whisper-small`, a Vietnamese automatic speech recognition model obtained by fine-tuning the multilingual `whisper-small` on a 3000-hour dataset (`PhoASR-3000h`). The model directly produces clean transcripts with reliable timestamps, punctuation and capitalization, eliminating the need for separate post-processing tools. Please **cite** our [PhoASR paper](https://aclanthology.org/2026.findings-eacl.345/) whenever `PhoASR-whisper-small` is used to produce published results or is incorporated into other software.

	@inproceedings{phoasr,
	    title = {{Vietnamese Automatic Speech Recognition: A Revisit}},
	    author = "Vu, Thi and Nguyen, Linh The and Nguyen, Dat Quoc",
	    booktitle = "Findings of the Association for Computational Linguistics: EACL 2026",
	    year = "2026",
	    pages = "6557--6568"
	}

## Model Inference with `transformers` 

```python
# INSTALLATION: pip install transformers==4.48.0

import torch
from transformers import pipeline

# Load the model
model_id = "Qualcomm-AI-Research/PhoASR-whisper-small"
device = "cuda" if torch.cuda.is_available() else "cpu"

# Create pipeline for automatic speech recognition with word-level timestamps
pipe = pipeline("automatic-speech-recognition", model=model_id, chunk_length_s=30, device=device, return_timestamps="word", generate_kwargs={"language": "vi"})

# Transcribe a single audio file
audio_path = "path-to-audio-sample.wav"
result = pipe(audio_path)

# Print full transcription
print(f"Full Text: {result['text']}")
# Print word-level timestamps
print(result['chunks'])
```

For more low-level control, please see [inference.py](https://huggingface.co/Qualcomm-AI-Research/PhoASR-whisper-small/blob/main/inference.py).

## License/Terms of Use
This model is released under the BSD 3-Clause Clear license and the Qualcomm responsible AI license: [https://www.qualcomm.com/site/responsible-ai-license](https://www.qualcomm.com/site/responsible-ai-license).

## Uses
The model is intended for research and educational purposes.

## Limitations and Bias
`PhoASR-3000h` is a variant of the `PhoASR-3100h` dataset (described in our [paper](https://aclanthology.org/2026.findings-eacl.345/) above), excluding 100 hours of audio originally released under a CC-BY-NC-ND 4.0 license. Because only a relatively small portion of `PhoASR-3000h` contains Central regional accents, `PhoASR-whisper-small` may show reduced accuracy for Central Vietnamese speakers and other underrepresented dialects. It may also struggle to recognize emerging or rare terminology.