import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np

class TrainedSVM:
  def __init__(self):
    self.train()
  def predict(self, x):
    x = self.std.transform([x])
    return self.svm.predict(x)
  def train(self):
    # Load Data
    df = pd.read_csv("./model/data.csv")
    X = df.iloc[:, :-1]
    Y = df["label"]
    # Data preprocessing
    std = StandardScaler()
    std.fit(X)
    X = std.transform(X)
    X_train, X_test , Y_train, Y_test = train_test_split(X, Y , random_state=1, train_size=0.8, stratify=Y)
    # Trained svm
    dims = []
    corrects = []
    best_dim = 0
    best_correct = 0
    for dim in np.arange(5, -5, 0.1):
      svm = SVC(C=(10** dim), random_state=1).fit(X_train, Y_train)
      correct = svm.score(X_test, Y_test)
      if correct > best_correct:
        best_correct = correct
        best_dim = dim
      dims.append(dim)
      corrects.append(correct)
    # Storage Best Model
    svm = SVC(C=(10**best_dim), random_state=1).fit(X_train , Y_train)
    self.svm = svm
    self.std = std
