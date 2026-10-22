# SilentLink — Dataset Layout and Preparation

This folder is the landing place for all datasets used by the training
scripts. No image or sequence data ships with the SilentLink repository — the
files you see here are documentation and placeholder directories only. Every
training script validates that the expected layout exists on disk before
running and raises a clear error pointing to this README when something is
missing. The two independent dataset pipelines (static alphabet images and
dynamic sign sequences) are described below, followed by the end-to-end
alphabet pipeline and pointers to well-known public datasets you can
download.

## Static Alphabet Image Dataset

The static fingerspelling model expects a folder of per-class images under
`data/asl_alphabet_train/<CLASS>/<image>.jpg`. Each sub-folder name is used
as the class label, so for the standard American Sign Language alphabet you
will create folders named `A`, `B`, `C`, ..., `Z`, plus optional helper
folders such as `del`, `nothing`, and `space` to represent non-letter rest
poses or editing actions. File names inside each class folder are not
important as long as they end in `.jpg`, `.jpeg`, or `.png`; the extraction
script sorts them and optionally caps the count with `--samples`. The
de-facto reference for this layout is the public "ASL Alphabet" dataset on
Kaggle (2019, ~87,000 JPEGs across 29 folders of 200×200px crops), which is
what the extraction defaults and helper comments were written against. Any
similarly structured folder of per-letter hand photos will work; MediaPipe
Hands is robust to a wide range of backgrounds and lighting.

## Dynamic Sign Sequences Dataset

The BiLSTM dynamic-sign model reads NumPy arrays from
`<seq-dataset>/sequences/<sign>/sample_XXXX.npy`. Each `.npy` file holds a
single sample of shape `(seq_len, 21, 3)` — 21 MediaPipe xyz hand landmarks
per frame, across `seq_len` consecutive frames of a sign being performed.
(The training script also accepts the flattened shape `(seq_len, 63)` since
the two are equivalent.) The folder name directly under `sequences/` is the
class label for every `.npy` sample inside it. Sample files should be named
consecutively such as `sample_0001.npy`, `sample_0002.npy` to keep ordering
deterministic, though any `.npy` filename is accepted. Shorter sequences are
zero-padded on the right to `--seq-len` and longer sequences are truncated,
so it is fine if your raw footage varies slightly in duration. To convert
raw video clips into this layout, run MediaPipe Hands frame-by-frame, keep
the first detected hand's landmark array, and save the stacked result with
`np.save`.

## End-to-End Alphabet Pipeline (Extract → Train → Evaluate)

The static fingerspelling pipeline is three commands. Step one:
`python training/extract_landmarks.py --data data/asl_alphabet_train --out data/asl_landmarks.npz --samples 400`
walks each class folder, runs MediaPipe on every image, normalizes the 63
landmark features wrist-relative, and writes a compressed `.npz` with keys
`X`, `y`, and `class_names`. Step two:
`python training/train_alphabet.py --data data/asl_landmarks.npz --out models/alphabet_mlp.json`
performs a stratified train/validation split with seed 42, fits a
scikit-learn MLP with early stopping, and serializes weights + scaler to the
JSON model card. Step three:
`python training/evaluate_alphabet.py --model models/alphabet_mlp.json --data data/asl_landmarks.npz`
re-applies the *exact same* split, runs the pure-NumPy forward pass used at
runtime, and writes accuracy, per-class precision/recall, top confusions,
and the full confusion matrix back into the JSON model card so metrics live
next to weights. On Windows you can replace the three manual commands with
the single launcher `scripts/train_alphabet.ps1`, which uses the virtual
environment if present and prints colored progress banners.

## Honest Disclosure: No Data Ships, and Where to Download Yours

SilentLink ships with zero image data and zero sequence data. Repositories
that bundle sign-language datasets are rare because the files are large and
licensing varies, so we instead point you at known public sources. For the
static alphabet, search for *"ASL Alphabet dataset Kaggle"* — the canonical
entry is ~1 GB and is licensed CC0-style for research and education. For
dynamic sign sequences the most established public collections are *WLASL*
(Word-Level American Sign Language, with 2000+ classes of YouTube-sourced
clips), *ASLLVD* (ASL Lexicon Video Dataset from Boston University), and
*MS-ASL* from Microsoft Research. Each of these publishes raw video; from
there you must run MediaPipe frame-by-frame to produce the
`sequences/<sign>/sample_XXXX.npy` layout expected by
`train_dynamic_signs.py`. All of the training scripts in SilentLink will
explicitly fail with a message that includes the words "dataset" and
"download" until the required files are present on your machine.
