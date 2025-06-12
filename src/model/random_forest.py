from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.multioutput import MultiOutputClassifier


# 模型训练
def train_model(X, y):

    # 创建多输出分类器
    model = MultiOutputClassifier(
        estimator=RandomForestClassifier(n_estimators=100)
    )

    # 一起训练两个任务
    model.fit(X, y)
    return model

# 在已有模型上训练
def train_model_base_on(X, y, model):
    # 训练模型
    model.fit(X, y)
    return model





