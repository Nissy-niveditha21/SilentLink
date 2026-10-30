import numpy as np

from training.train_dynamic_signs import _load_seq_dataset


def test_loader_preserves_official_wlasl_splits(tmp_path):
    root = tmp_path / "dataset"
    for split in ("train", "val", "test"):
        directory = root / "sequences" / "hello" / split
        directory.mkdir(parents=True)
        np.save(directory / "sample.npy", np.ones((3, 21, 3), dtype=np.float32))

    X, y, class_names, splits = _load_seq_dataset(str(root), seq_len=4)

    assert X.shape == (3, 4, 63)
    assert y.tolist() == [0, 0, 0]
    assert class_names == ["hello"]
    assert splits.tolist() == ["train", "val", "test"]
    assert np.all(X[:, 3, :] == 0)
