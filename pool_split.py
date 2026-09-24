"""
pool_split.py —— 每日瓜分奖池的分账逻辑

原始未修改版本（用于复现问题与测试对照）
"""


def split_pool(pool_cents: int, weights: list[int]) -> list[int]:
    """把 pool_cents 按 weights 的比例分给每个人，返回每人拿到多少分。

    返回列表与 weights 一一对应。
    """
    total = sum(weights)
    return [round(pool_cents * w / total) for w in weights]


if __name__ == "__main__":
    # 一个跑得通的例子：奖池 100 元，三个人权重相同
    print(split_pool(10000, [1, 1, 1]))
