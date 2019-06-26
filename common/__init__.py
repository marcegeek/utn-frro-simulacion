import collections
import copy
import functools

import numpy as np
import matplotlib.pyplot as plt


class RandomPopulation:

    def __init__(self, population):
        self._population = np.array(population)

    @property
    def population(self):
        return self._population.copy()

    @property
    def classes(self):
        n = len(self._population)
        sq = np.sqrt(n)
        return int(np.ceil(sq))

    def plot_histogram(self):
        plt.hist(self._population, bins=self.classes, density=True)
        plt.grid()

    def frequency_distribution(self):
        return FrequencyDistribution(values=self._population, classes=self.classes)


@functools.total_ordering
class FrequencyDistributionEntry:

    def __init__(self, val, freq):
        if isinstance(val, collections.Iterable):
            val = tuple(val)
        self.val = val
        self.freq = freq

    def is_continuous(self):
        return isinstance(self.val, tuple)

    def is_discrete(self):
        return not self.is_continuous()

    def __str__(self):
        return '{}: {}'.format(self.val, self.freq)

    def __eq__(self, other):
        if self.is_continuous():
            if not np.isclose(self.val, other.val, atol=0.00001, rtol=0.00001).all():
                return False
        else:
            if not np.isclose(self.val, other.val, atol=0.00001, rtol=0.00001):
                return False
        return np.isclose(self.freq, other.freq, atol=0.00001, rtol=0.00001)

    def __lt__(self, other):
        return (self.val, self.freq) < (other.val, other.freq)


class FrequencyDistribution(collections.Sequence):

    def __init__(self, values=None, classes=None, distr=None):
        self._distribution = None
        if values is not None:
            self._init_from_values(values, classes)
        elif distr is not None:
            self._distribution = copy.deepcopy(distr)
            self._distribution.sort()
            self._normalize()
            self.discrete = len([e for e in self._distribution if e.is_discrete()]) != 0
            if self.is_discrete():
                for e in self._distribution:
                    e.val = int(e.val)

    def _init_from_values(self, values, classes):
        arr = np.array(values)
        if arr.dtype.kind == 'i':  # distribución discreta
            self.discrete = True
            self._distribution = [
                FrequencyDistributionEntry(v, f)
                for v, f in zip(*np.unique(arr, return_counts=True))
            ]
        else:  # distribución continua
            self.discrete = False
            if classes is None:
                classes = int(np.ceil(np.sqrt(len(arr))))
            partition_values = np.linspace(arr.min(), arr.max(), classes + 1)
            self._distribution = []
            for i in range(classes):
                bool_matches = np.logical_and(arr >= partition_values[i],
                                              arr < partition_values[i + 1])
                count = len(np.where(bool_matches)[0])
                if i == classes - 1:  # el último intervalo es cerrado
                    extra_matches = (arr == partition_values[classes])
                    count += len(np.where(extra_matches)[0])
                entry = FrequencyDistributionEntry((partition_values[i], partition_values[i + 1]),
                                                   count)
                self._distribution.append(entry)
        self._normalize()

    def is_continuous(self):
        return not self.is_discrete()

    def is_discrete(self):
        return self.discrete

    @property
    def distribution(self):
        return copy.deepcopy(self._distribution)

    @property
    def values(self):
        return np.array([e.val for e in self._distribution])

    @property
    def frequencies(self):
        return np.array([e.freq for e in self._distribution])

    def get_freq(self, x):
        i = self._get_index(x)
        if i is not None:
            return self._distribution[i].freq

    def _get_index(self, x):
        for i in range(len(self)):
            e = self._distribution[i]
            if self.is_continuous():
                if (e.val[0] <= x < self[i].val[1] or
                        i == len(self) - 1 and x == e.val[1]):
                    return i
            else:
                if e.val == x:
                    return i

    def cumulative_distribution(self):
        return self.frequencies.cumsum()

    def _normalize(self):
        # normalizar frecuencias entre 0 y 1
        ac = self.frequencies.sum()
        for e in self._distribution:
            e.freq /= ac

    def __getitem__(self, index):
        return copy.deepcopy(self._distribution[index])

    def __len__(self):
        return len(self._distribution)