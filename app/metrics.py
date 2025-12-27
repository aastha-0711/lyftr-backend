from collections import defaultdict

_metrics = defaultdict(int)


def inc(name: str):
    _metrics[name] += 1


def snapshot():
    return dict(_metrics)
