import numpy as np
from decision_tree import CustomDecisionTreeClassifier
from typing import Optional
from pathos.multiprocessing import ProcessingPool as Pool
from pathos.helpers import cpu_count

class CustomRandomForestClassifier:
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: float = np.inf,
        min_samples_split: int = 2,
        criterion: str = 'gini',
        bootstrap: bool = True,
        max_features=None,
        random_state: Optional[int] = None,
        n_jobs: int = -1
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.criterion = criterion
        self.bootstrap = bootstrap
        self.random_state = random_state
        self.n_jobs = n_jobs
        self.max_features = max_features

        self.trees = []

        if random_state is not None:
            np.random.seed(random_state)

    def fit(self, X, y):
        X = np.array(X)
        y = np.array(y).astype(int)
        n_samples = X.shape[0]

        self.trees = []

        def train_tree(_):
            tree = CustomDecisionTreeClassifier(
                criterion=self.criterion,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                max_features=self.max_features
            )
            if self.bootstrap:
                idx = np.random.randint(0, n_samples, size=n_samples)
            else:
                idx = np.arange(n_samples)
            X_res = X[idx]
            y_res = y[idx]

            tree.fit(X_res, y_res)
            return tree

        if self.n_jobs == -1:
            n_jobs = cpu_count()
        else:
            n_jobs = self.n_jobs

        with Pool(processes=n_jobs) as pool:
            self.trees = pool.map(train_tree, range(self.n_estimators))
        
        return self

    def prune(self, X, y, X_val, y_val, alpha_crit=np.inf, max_prune_steps=50):
            def prune_tree(tree):
                tree.ccp(X, y, X_val, y_val, alpha_crit, max_prune_steps)
                return tree

            if self.n_jobs == -1:
                n_jobs = cpu_count()
            else:
                n_jobs = self.n_jobs

            with Pool(processes=n_jobs) as pool:
                self.trees = pool.map(prune_tree, self.trees)
                
    def predict(self, X):
        X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        def predict_tree(tree):
            return tree.predict(X)

        if self.n_jobs == -1:
            n_jobs = cpu_count()
        else:
            n_jobs = self.n_jobs

        with Pool(processes=n_jobs) as pool:
            predictions_list = pool.map(predict_tree, self.trees)
        predictions = np.array(predictions_list)
        
        n_samples = X.shape[0]
        final_predictions = np.empty(n_samples, dtype=int)
        for i in range(n_samples):
            final_predictions[i] = np.bincount(predictions[:, i]).argmax()
        
        return final_predictions