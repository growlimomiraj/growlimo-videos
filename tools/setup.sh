#!/bin/bash
# One-time setup in a fresh workspace: Python deps + Kokoro TTS (with the duration output used for caption timing).
set -e
pip install --break-system-packages -q kokoro-onnx soundfile opencv-python-headless onnx playwright scipy pillow 2>&1 | tail -1 || true
TTS=${TTS_DIR:-/home/claude/tts}; mkdir -p "$TTS"; cd "$TTS"
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -f kokoro-v1.0.onnx ] || curl -sSL -o kokoro-v1.0.onnx $B/kokoro-v1.0.onnx
[ -f voices-v1.0.bin ] || curl -sSL -o voices-v1.0.bin $B/voices-v1.0.bin
[ -f kokoro-dur.onnx ] || python3 - <<'EOF'
import onnx
m=onnx.load('kokoro-v1.0.onnx')
vi=onnx.helper.make_tensor_value_info('/encoder/Clip_output_0',onnx.TensorProto.FLOAT,None)
# the duration tensor may be int64 in some exports; let shape inference decide if float fails
m.graph.output.append(vi)
try:
    onnx.save(m,'kokoro-dur.onnx')
except Exception as e:
    print('save failed',e)
EOF
python3 -c "
import onnxruntime as ort; s=ort.InferenceSession('$TTS/kokoro-dur.onnx'); print('outputs',[o.name for o in s.get_outputs()])"
ls -la "$TTS"
