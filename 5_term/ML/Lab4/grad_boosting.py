import numpy as np
from decision_tree import CustomDecisionTreeClassifier, DecisionTreeNode
from typing import Optional
from pathos.multiprocessing import ProcessingPool as Pool
from pathos.helpers import cpu_count
import time


class CustomGradientBoostingClassifier:
    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        subsample: float = 1.0,
        max_depth: float = 3,
        min_samples_split: int = 2,
        max_features=None,
        random_state: Optional[int] = None,
        n_jobs: int = -1
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state
        self.n_jobs = n_jobs

        self.trees = []
        self.initial_prediction = None
        self.classes_ = None

        if random_state is not None:
            np.random.seed(random_state)

    def _softmax(self, scores):
        max_scores = np.max(scores, axis=1, keepdims=True)
        exp_scores = np.exp(scores - max_scores)
        return exp_scores / np.sum(exp_scores, axis=1, keepdims=True)

    def _regression_gain(self, y, y_false, y_true):
        n = len(y)
        if n == 0:
            return 0.0
        n_false = len(y_false)
        n_true = len(y_true)

        parent_var = np.var(y)
        weighted_var = (n_false / n) * np.var(y_false) + (n_true / n) * np.var(y_true)
        return parent_var - weighted_var

    def _get_leaf_by_id(self, x, root: DecisionTreeNode):
        current = root
        while current.leaf_value is None:
            if x[current.feature_idx] >= current.threshold:
                current = current.true_branch
            else:
                current = current.false_branch
        return id(current)

    def _update_leaf_value(self, x_example, root: DecisionTreeNode, target_id, new_value):
        current = root
        while current.leaf_value is None:
            if x_example[current.feature_idx] >= current.threshold:
                current = current.true_branch
            else:
                current = current.false_branch
        if id(current) == target_id:
            current.leaf_value = new_value

    def fit(self, X, y):
        X = np.array(X)
        y = np.array(y).astype(int)

        start_time = time.time()
        
        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        class_to_idx = {c: i for i, c in enumerate(self.classes_)}
        y_idx = np.array([class_to_idx[c] for c in y])
        y_onehot = np.eye(n_classes)[y_idx]

        priors = np.mean(y_onehot, axis=0)
        self.initial_prediction = np.log(priors + 1e-10)

        current_scores = np.tile(self.initial_prediction, (X.shape[0], 1))

        self.trees = [[] for _ in range(n_classes)]

        n_samples = X.shape[0]
        sample_size = int(self.subsample * n_samples) if self.subsample < 1.0 else n_samples

        for m in range(self.n_estimators):
            elapsed = time.time() - start_time
            avg_time = elapsed / (m + 1)
            remaining = avg_time * (self.n_estimators - m - 1)
            print(f"Tree {m+1}/{self.n_estimators} | Passed: {elapsed:.1f}с | Left: {remaining:.1f}с", flush=True)

            probs = self._softmax(current_scores)
            residuals = y_onehot - probs

            if self.subsample < 1.0:
                idx = np.random.choice(n_samples, sample_size, replace=False)
            else:
                idx = np.arange(n_samples)

            X_sub = X[idx]
            residuals_sub = residuals[idx]

            stage_trees = []
            for k in range(n_classes):
                tree = CustomDecisionTreeClassifier(
                    criterion='gini',
                    max_depth=self.max_depth,
                    min_samples_split=self.min_samples_split,
                    max_features=self.max_features,
                    random_state=self.random_state + m * n_classes + k if self.random_state is not None else None
                )

                tree._get_info_gain = lambda yp, yf, yt: self._regression_gain(yp, yf, yt)
                tree._count_leaf_value = lambda yp: np.mean(yp)

                tree.fit(X_sub, residuals_sub[:, k])
                stage_trees.append(tree)

            for k, tree in enumerate(stage_trees):
                leaf_ids = np.array([self._get_leaf_by_id(x, tree.tree) for x in X])
                unique_leaf_ids = np.unique(leaf_ids)

                for leaf_id in unique_leaf_ids:
                    mask = (leaf_ids == leaf_id)
                    if not np.any(mask):
                        continue

                    r_leaf = residuals[mask, k]
                    p_leaf = probs[mask, k]

                    numerator = np.sum(r_leaf)
                    denominator = np.sum(p_leaf * (1 - p_leaf)) + 1e-10
                    gamma = numerator / denominator

                    sample_x = X[mask][0]
                    self._update_leaf_value(sample_x, tree.tree, leaf_id, gamma)

            for k, tree in enumerate(stage_trees):
                update = tree.predict(X)
                current_scores[:, k] += self.learning_rate * update

            for k in range(n_classes):
                self.trees[k].append(stage_trees[k])

        return self

    def predict_proba(self, X):
        X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]
        scores = np.tile(self.initial_prediction, (n_samples, 1))

        for m in range(self.n_estimators):
            for k in range(len(self.classes_)):
                tree = self.trees[k][m]
                scores[:, k] += self.learning_rate * tree.predict(X)

        return self._softmax(scores)

    def predict(self, X):
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]