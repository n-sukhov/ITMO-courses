from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Any, Optional
import copy

@dataclass
class DTNodeParameters:
    information_gain : float = None
    threshold : float = None
    feature_idx : int = None

@dataclass
class DecisionTreeNode(DTNodeParameters):
    true_branch : DecisionTreeNode = None
    false_branch : DecisionTreeNode = None

    leaf_value : Any = None # When the node is a leaf

    @classmethod
    def from_params(cls, params: DTNodeParameters, true_branch=None, false_branch=None):
        return cls(
            information_gain=params.information_gain,
            threshold=params.threshold,
            feature_idx=params.feature_idx,
            true_branch=true_branch,
            false_branch=false_branch
        )

class CustomDecisionTreeClassifier:
    def __init__(
        self,
        criterion='gini',
        max_depth=np.inf,
        min_samples_split=2,
        max_features=None,
        random_state: Optional[int] = None
    ):
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.tree = None

        if random_state is not None:
            np.random.seed(random_state)

    def _get_feature_subset(self, features_num):
        if self.max_features is None:
            return features_num
        elif self.max_features == 'sqrt':
            return int(np.sqrt(features_num))
        elif self.max_features == 'log2':
            return int(np.log2(features_num))
        elif isinstance(self.max_features, int):
            return min(self.max_features, features_num)
        elif isinstance(self.max_features, float) and self.max_features < 1.0:
            return int(self.max_features * features_num)
        else:
            return features_num
    
    def _get_class_boundary_thresholds(self, feature_values, y):
        sorted_indices = np.argsort(feature_values)
        sorted_features = feature_values[sorted_indices]
        sorted_y = y[sorted_indices]
        
        boundaries = []
        
        for i in range(1, len(sorted_features)):
            if sorted_y[i] != sorted_y[i-1]:
                threshold = (sorted_features[i] + sorted_features[i-1]) / 2.0
                boundaries.append(threshold)

        return np.unique(boundaries)
    
    def _find_best_split(self, X, y, features_num) -> tuple:
        best_split = DTNodeParameters(information_gain=0)
        best_mask = None
        n_features_to_try = self._get_feature_subset(features_num)

        if n_features_to_try < features_num:
            feature_indices = np.random.choice(features_num, size=n_features_to_try, replace=False)
        else:
            feature_indices = range(features_num)

        for feature_idx in feature_indices:
            values = X[:, feature_idx]
            thresholds = self._get_class_boundary_thresholds(values, y)

            for threshold in thresholds:
                mask = values >= threshold
                y_true = y[mask]
                y_false = y[~mask]

                if len(y_false) > 0 and len(y_true) > 0:
                    new_info_gain = self._get_info_gain(y, y_false, y_true)
                    if new_info_gain > best_split.information_gain:
                        best_split.information_gain = new_info_gain
                        best_split.threshold = threshold
                        best_split.feature_idx = feature_idx
                        best_mask = mask

        if best_mask is not None:
            return best_split, best_mask
        else:
            return best_split, None     

    def _get_info_gain(self, y, y_false, y_true) -> float:
        n = len(y)
        n_false = len(y_false)
        n_true = len(y_true)

        def impurity(arr):
            unique, counts = np.unique(arr, return_counts=True)
            p = counts / len(arr)
            p = p[p > 0]
            match self.criterion:
                case'gini':
                    return 1 - np.sum(p ** 2)
                case 'entropy':
                    return -np.sum(p * np.log2(p))

        parent_imp = impurity(y)
        false_imp = impurity(y_false)
        true_imp = impurity(y_true)
        weighted_imp = (n_false / n) * false_imp + (n_true / n) * true_imp
        return parent_imp - weighted_imp

    def _count_leaf_value(self, y):
        unique, counts = np.unique(y, return_counts=True)
        return unique[np.argmax(counts)]

    def _build_tree(self, X, y, current_depth=0) -> DecisionTreeNode:
        samples_num, features_num = np.shape(X)

        if current_depth < self.max_depth and samples_num >= self.min_samples_split:
            node_params, mask = self._find_best_split(X, y, features_num)
            if node_params.information_gain > 0:
                true_branch = self._build_tree(X[mask], y[mask], current_depth=current_depth+1)
                false_branch = self._build_tree(X[~mask], y[~mask], current_depth=current_depth+1)
                
                return DecisionTreeNode.from_params(
                    params=node_params,
                    true_branch=true_branch,
                    false_branch=false_branch
                )
            
        return DecisionTreeNode(leaf_value=self._count_leaf_value(y))

    def _count_leaves(self, t_node):
        if t_node.leaf_value is not None:
            return 1
        return self._count_leaves(t_node.true_branch) + self._count_leaves(t_node.false_branch)

    def _R(self, t_node, X, y, as_leaf=False):
        if as_leaf:
            unique, counts = np.unique(y, return_counts=True)
            pred = unique[np.argmax(counts)]
            return np.sum(y != pred)
        
        if t_node.leaf_value is not None:
            y_pred = t_node.leaf_value
            return np.sum(y != y_pred)

        mask = X[:, t_node.feature_idx] >= t_node.threshold

        X_true, y_true = X[mask], y[mask]
        X_false, y_false = X[~mask], y[~mask]

        return self._R(t_node.true_branch, X_true, y_true) + \
               self._R(t_node.false_branch, X_false, y_false)

    def _alpha_t(self, t_node, X, y):
        R_subtree = self._R(t_node, X, y)
        R_leaf = self._R(t_node, X, y, as_leaf=True)
        leaves = self._count_leaves(t_node)

        if leaves <= 1:
            return np.inf

        return (R_leaf - R_subtree) / (leaves - 1)
    
    def _get_alphas(self, node, X, y, result):
        if node is None:
            return
        alpha = self._alpha_t(node, X, y)

        if node.leaf_value is None and alpha != np.inf:
            result.append((alpha, node))

        if node.leaf_value is None:
            mask = X[:, node.feature_idx] >= node.threshold
            self._get_alphas(node.true_branch, X[mask], y[mask], result)
            self._get_alphas(node.false_branch, X[~mask], y[~mask], result)

    def prune_node(self, node, y_sub):
        node.true_branch = None
        node.false_branch = None
        node.leaf_value = self._count_leaf_value(y_sub)

    def _get_sub_y(self, node, node_to_prune, X, y):
        if node == node_to_prune:
            return y
        
        if node.leaf_value is not None:
            return np.array([], dtype=y.dtype)
        
        mask = X[:, node.feature_idx] >= node.threshold
        return np.concatenate([
            self._get_sub_y(node.true_branch, node_to_prune, X[mask], y[mask]),
            self._get_sub_y(node.false_branch, node_to_prune, X[~mask], y[~mask])
        ])
        
    def ccp(self, X_train, y_train, X_val, y_val, alpha_crit=np.inf, max_prune_steps=50):
        best_tree = copy.deepcopy(self.tree)
        best_score = np.mean(self.predict(X_val) != y_val)

        steps = 0
        while steps < max_prune_steps:
            steps += 1
            alphas = []
            self._get_alphas(best_tree, X_train, y_train, alphas)
            if not alphas:
                break

            alphas.sort(key=lambda x: x[0])
            alpha, node_to_prune = alphas[0]
            if alpha >= alpha_crit:
                break

            y_sub = self._get_sub_y(best_tree, node_to_prune, X_train, y_train)
            self.prune_node(node_to_prune, y_sub)

            score = np.mean(np.array([self._traverse_tree(x, best_tree) for x in X_val]) != y_val)

            if score < best_score:
                best_score = score
                self.tree = copy.deepcopy(best_tree)

    def fit(self, X, y):
        X = np.array(X)
        y = np.array(y)
        if len(X) != len(y):
            raise ValueError("X and y must have the same length!")
        self.tree = self._build_tree(X, y)

    def _traverse_tree(self, x, node: DecisionTreeNode):
        current_node = node
        while current_node.leaf_value is None:
            if x[current_node.feature_idx] >= current_node.threshold:
                current_node = current_node.true_branch
            else:
                current_node = current_node.false_branch
        return current_node.leaf_value
        
    def predict(self, X):
        X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return np.array([self._traverse_tree(x, self.tree) for x in X])