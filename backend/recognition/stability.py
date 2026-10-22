from collections import deque, Counter


class PredictionStabilizer:
    def __init__(self, window_size=15, min_count=10):
        self.window = deque(maxlen=window_size)
        self.min_count = min_count
        self.last_confirmed = None

    def add_prediction(self, prediction):
        self.window.append(prediction)

        if len(self.window) < self.window.maxlen:
            return None

        counter = Counter(self.window)
        most_common, count = counter.most_common(1)[0]

        if count >= self.min_count and most_common != self.last_confirmed:
            self.last_confirmed = most_common
            self.window.clear()
            return most_common

        return None
