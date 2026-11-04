"""Train and compare scikit-learn gesture classifiers on hand-landmark data.

The input is a CSV in the MediaPipe hand-gesture dataset format
(kinivi / Kazuhito00):

    * ``keypoint.csv``                  - column 0 = class id, columns 1.. = 42 features
    * ``keypoint_classifier_label.csv`` - one label name per line (row = class id)

The script trains and evaluates an SVM, a KNN and a small MLP (a neural network),
picks the best by macro F1, and saves it as a joblib bundle that the app loads.

Usage:
    python tools/train_model.py                     # uses data/raw
    python tools/train_model.py --data path/to/dir
    python tools/train_model.py --data keypoint.csv --labels labels.csv
"""

import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gesture_control import config, features  # noqa: E402

from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.neighbors import KNeighborsClassifier  # noqa: E402
from sklearn.neural_network import MLPClassifier  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import LabelEncoder, StandardScaler  # noqa: E402
from sklearn.svm import SVC  # noqa: E402

SEED = 42


def _find_csvs(path):
    if os.path.isdir(path):
        return glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)
    return [path]


def load_dataset(path, labels_path=None, drop_z=None):
    """Load features + labels from a keypoint CSV (or a directory of CSVs)."""
    csvs = _find_csvs(path)
    if not csvs:
        raise FileNotFoundError("No CSV files found under {}".format(path))

    label_csv = labels_path
    for f in csvs:
        if "label" in os.path.basename(f).lower() and label_csv is None:
            label_csv = f

    data_csv = None
    for f in csvs:
        name = os.path.basename(f).lower()
        if "label" in name:
            continue
        if data_csv is None or "keypoint" in name:
            data_csv = f
    if data_csv is None:
        raise FileNotFoundError("No keypoint/data CSV found under {}".format(path))

    raw = pd.read_csv(data_csv, header=None)
    label_column = raw.iloc[:, 0]
    feature_frame = raw.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    mask = feature_frame.notna().all(axis=1)
    label_column = label_column[mask].reset_index(drop=True)
    X = feature_frame[mask].to_numpy(dtype=float)

    label_names = None
    if label_csv is not None:
        label_names = pd.read_csv(label_csv, header=None).iloc[:, 0].astype(str).tolist()

    y = []
    for value in label_column.tolist():
        if label_names is not None:
            try:
                y.append(label_names[int(float(value))])
            except (ValueError, IndexError):
                y.append(str(value))
        else:
            y.append(str(value))
    y = np.array(y)

    if drop_z is None:
        drop_z = X.shape[1] == 63
    if drop_z and X.shape[1] % 3 == 0:
        keep = [i for i in range(X.shape[1]) if i % 3 != 2]
        X = X[:, keep]

    if X.shape[1] != features.FEATURE_DIM:
        raise ValueError(
            "Expected {} features but the dataset has {}. Adjust preprocessing or "
            "the --drop-z option.".format(features.FEATURE_DIM, X.shape[1])
        )

    print("Loaded {} samples, {} classes, {} features from {}".format(
        len(y), len(set(y)), X.shape[1], os.path.basename(data_csv)))
    return X, y


def build_models():
    return {
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(kernel="rbf", C=10, gamma="scale", random_state=SEED)),
        ]),
        "knn": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", KNeighborsClassifier(n_neighbors=5)),
        ]),
        "mlp": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=1000,
                                  early_stopping=True, random_state=SEED)),
        ]),
    }


def evaluate(model, X_test, y_test):
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, predictions, average="macro", zero_division=0)
    matrix = confusion_matrix(y_test, predictions)
    return accuracy, precision, recall, f1, matrix


def save_confusion_matrix(matrix, labels, name, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    fig, ax = plt.subplots(figsize=(1.4 * len(labels) + 2, 1.2 * len(labels) + 2))
    ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix - {}".format(name))
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, matrix[i, j], ha="center", va="center", color="black")
    fig.tight_layout()
    path = os.path.join(out_dir, "confusion_matrix_{}.png".format(name))
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description="Train gesture classifiers on landmark data.")
    parser.add_argument("--data", default=config.RAW_DATA_DIR,
                        help="keypoint CSV or a directory containing it")
    parser.add_argument("--labels", default=None, help="optional label CSV path")
    parser.add_argument("--out", default=config.MODEL_PATH, help="output joblib path")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--drop-z", action="store_true", default=None,
                        help="drop z coordinates (auto-detected for 63-feature files)")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    X, y = load_dataset(args.data, args.labels, args.drop_z)

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)
    labels = encoder.classes_.tolist()

    stratify = y_encoded if min(np.bincount(y_encoded)) >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=args.test_size, random_state=args.seed, stratify=stratify)

    out_dir = os.path.dirname(args.out)
    os.makedirs(out_dir, exist_ok=True)

    print("\nTraining {} models on {} train / {} test samples...".format(
        len(build_models()), len(X_train), len(X_test)))
    print("{:<6} {:>10} {:>10} {:>10} {:>8}".format("model", "accuracy", "precision", "recall", "f1"))

    results = {}
    best_name = None
    best_f1 = -1.0
    for name, model in build_models().items():
        model.fit(X_train, y_train)
        accuracy, precision, recall, f1, matrix = evaluate(model, X_test, y_test)
        results[name] = {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "confusion_matrix": matrix.tolist(),
        }
        print("{:<6} {:>10.4f} {:>10.4f} {:>10.4f} {:>8.4f}".format(
            name, accuracy, precision, recall, f1))
        save_confusion_matrix(matrix, labels, name, out_dir)
        if f1 > best_f1:
            best_f1 = f1
            best_name = name
            best_model = model

    import joblib
    joblib.dump(
        {"model": best_model, "labels": labels, "feature_dim": features.FEATURE_DIM,
         "classifier": best_name},
        args.out,
    )

    metrics = {
        "best": best_name,
        "labels": labels,
        "feature_dim": features.FEATURE_DIM,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "results": results,
    }
    with open(config.METRICS_PATH, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    print("\nBest model: {} (macro F1 = {:.4f})".format(best_name, best_f1))
    print("Saved model   -> {}".format(args.out))
    print("Saved metrics -> {}".format(config.METRICS_PATH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
