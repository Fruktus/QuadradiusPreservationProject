import math


class FullBinaryTreeIndexer:
    levels: int

    def __init__(self, min_leaves: int):
        if min_leaves < 1:
            raise ValueError('tree needs to have at least one element')
        rounded = 1 << (min_leaves - 1).bit_length()  # Round up leaves to the nearest power of 2
        self.levels = int(math.log2(rounded)) + 1

    @property
    def leaves(self) -> int:
        return 2 ** (self.levels - 1)

    def get_node_count(self) -> int:
        return (self.leaves * 2) - 1

    def get_nodes_at_level(self, level: int) -> list[int]:
        if level < 0 or level >= self.levels:
            raise ValueError(f'Level: {level} is out of bounds. Level count: {self.levels}')

        start = (1 << level) - 1
        end = (1 << (level + 1)) - 1
        return list(range(start, end))

    def get_node_parent(self, node_idx: int) -> int:
        last_node_index = self.get_nodes_at_level(self.levels-1)[-1]
        if node_idx <= 0 or node_idx > last_node_index:
            raise ValueError(
                f'Node index: {node_idx} is out of bounds. Last node index: {last_node_index} for {self.levels} levels.'
            )

        return (node_idx - 1) // 2
