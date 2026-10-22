# SilentLink — Model Artifacts

This folder stores the trained model JSON files used at runtime by the SilentLink
backend. Every model is shipped as plain JSON (no pickle, no HDF5, no TensorFlow
SavedModel) so the web server only depends on NumPy to run inference. No binary
weights are invented or committed to the repository — each file here is produced
by running the training pipeline on your own machine with a dataset you supply.
If a file is missing the runtime gracefully degrades: the app still starts, the
corresponding recognizer module returns an empty or "not loaded" result, and a
clear warning is emitted to the log.

## alphabet_mlp.json — Static Fingerspelling MLP

The file `alphabet_mlp.json` is produced by `training/train_alphabet.py` using a
scikit-learn `MLPClassifier` trained on 63 normalized hand-landmark features
(21 MediaPipe landmarks × 3 xyz coordinates, made wrist-relative and scaled by
the wrist-to-middle-MCP distance). The model is a small multi-layer perceptron
with ReLU hidden activations and a softmax output over ASL letter classes. After
training, the sklearn weights are extracted, paired with a `StandardScaler`, and
serialized to JSON. The evaluator script `training/evaluate_alphabet.py` then
fills in the `evaluation` sub-object with real held-out accuracy, per-class
precision/recall, and a confusion matrix so the file doubles as its own model
card. Top-level JSON keys are: `format` (always `"silentlink-alphabet-mlp-v1"`),
`classes` (ordered list of class-name strings), `hidden_sizes` (integer list of
hidden-layer widths), `scaler` (with `mean` and `scale` arrays of length 63),
`layers` (list of `{weights, bias}` objects where each `weights` is an
`[in][out]` matrix and `bias` is length `out`), and `evaluation` as filled by
the evaluator (or `null` if evaluation has not been run yet).

## dynamic_sign_lstm.json — Dynamic-Sign BiLSTM

The file `dynamic_sign_lstm.json` is the future output of
`training/train_dynamic_signs.py`. It represents a stacked bidirectional LSTM
followed by a linear classifier that maps a sequence of 63-dimensional
landmark vectors (one frame per timestep) to one of N dynamic sign classes such
as whole ASL words or phrases. The architecture is intentionally small and
runs comfortably on a laptop GPU or CPU. To plug the trained file into the
`DynamicSignRecognizer` at runtime, the module loads the JSON, rebuilds the
layer order from the saved `layers` list, and implements a hand-rolled NumPy
forward pass (sigmoid/tanh gates for each LSTM cell, concatenated
bidirectional outputs, then the final linear projection). The recognizer
expects the same `seq_len` and class ordering that were used at training time,
so both are stored directly in the JSON rather than re-derived. The backend
never imports PyTorch or TensorFlow; everything is NumPy arithmetic.

## Per-Key JSON Reference (so you can open the file and match the doc)

Every model file declares a `format` string first — this is the single version
check the runtime performs before trusting the rest of the payload. For the
alphabet MLP the next important keys are `scaler.mean` and `scaler.scale`,
which are applied element-wise to the 63-dimensional input before the first
matrix multiply. The `layers` array has one entry per weight-matrix layer of
the network: for a typical `[64, 32]` hidden MLP over 26 letters you will see
three entries (63→64, 64→32, 32→26). For the dynamic BiLSTM model the
`layers` array stores the LSTM gate weights and biases plus the final linear
projection, keyed by the exact state_dict names produced by PyTorch so a
student can cross-reference them against the PyTorch module definition. The
`classes` list is always the *ordered* list of class names; an argmax of the
model output at index `i` corresponds to `classes[i]`. Auxiliary keys like
`best_val_acc`, `train_time_s`, and `evaluation` are metadata — informative
but never read by the forward path.

## Loading Notes: Graceful Degradation and Zero TensorFlow Requirement

Runtime does NOT require TensorFlow, Keras, or PyTorch. The only heavyweight
dependency is NumPy, plus OpenCV and MediaPipe for the webcam capture that
produces landmarks in the first place. If `alphabet_mlp.json` is missing when
the backend starts, the `StaticSignRecognizer` logs a single warning and every
`predict()` call returns a confidence-less empty label; the rest of the app
(voice input, TTS, UI) continues to work. Similarly, if
`dynamic_sign_lstm.json` is absent, the dynamic-sign pipeline simply reports
"model not loaded" rather than crashing. This means the repo can be cloned and
run end-to-end for UI/UX work even before any training data has been assembled
on the developer's machine.
