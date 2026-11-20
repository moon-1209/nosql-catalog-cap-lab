"""Tách từ tiếng Việt bằng RDRSegmenter (VnCoreNLP, cần Java) theo khuyến nghị của PhoBERT (G18).

`segment("khoa tim mạch ở đâu")` ➔ "khoa tim_mạch ở đâu". Có cache trong bộ nhớ; JVM chỉ khởi động lần đầu gọi.
Văn bản đầu vào nên đã chuẩn hóa (text_norm.normalize) để câu train và câu chạy thật tách giống nhau.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from nlu import config

Backend = Callable[[str], list[str]]


def _vncorenlp_backend(vncorenlp_dir: Path) -> Backend:
    jar = vncorenlp_dir / "VnCoreNLP-1.2.jar"
    seg_model = vncorenlp_dir / "models" / "wordsegmenter" / "wordsegmenter.rdr"
    missing = [str(p) for p in (jar, seg_model) if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"VnCoreNLP files missing: {', '.join(missing)}")
    os.environ.setdefault("JAVA_HOME", config.DEFAULT_JAVA_HOME)
    if not Path(os.environ["JAVA_HOME"]).is_dir():
        raise FileNotFoundError(f"JAVA_HOME not found: {os.environ['JAVA_HOME']} (cần Java ≥ 8)")
    import py_vncorenlp

    # VnCoreNLP đọc model theo đường dẫn tương đối nên py_vncorenlp chdir vào save_dir và không chdir lại.
    cwd = os.getcwd()
    try:
        model = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=str(vncorenlp_dir))
    finally:
        os.chdir(cwd)
    return model.word_segment


class Segmenter:
    """`backend(text) -> list[câu đã tách]`; mặc định RDRSegmenter, tạo khi gọi lần đầu."""

    def __init__(self, backend: Backend | None = None, vncorenlp_dir: Path = config.VNCORENLP_DIR) -> None:
        self._backend = backend
        self._dir = vncorenlp_dir
        self._cache: dict[str, str] = {}
        self.backend_calls: int = 0

    def __call__(self, text: str) -> str:
        text = " ".join(text.split())
        if text == "":
            return ""
        if text not in self._cache:
            if self._backend is None:
                self._backend = _vncorenlp_backend(self._dir)
            self.backend_calls += 1
            self._cache[text] = " ".join(self._backend(text))
        return self._cache[text]


_default: Segmenter | None = None


def segment(text: str) -> str:
    global _default
    if _default is None:
        _default = Segmenter()
    return _default(text)
