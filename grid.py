from config import GRID_SIZE, WORLD_SIZE, WUMPUS_PROB, PIT_PROB
import random

# Initialize grid
grid = ['wall'] * (GRID_SIZE * GRID_SIZE)

# Generate Wumpus, Pit, and Gold
for y in range(1, WORLD_SIZE + 1):
    for x in range(1, WORLD_SIZE + 1):
        grid_y = GRID_SIZE - y - 1
        index = grid_y * GRID_SIZE + x
        grid[index] = 'empty'

        if index == 25:  # (1,1)에는 생성 X
            continue

        has_wumpus = random.random() < WUMPUS_PROB
        has_pit = random.random() < PIT_PROB

        if has_pit:
            grid[index] = 'pit'
        elif has_wumpus:
            grid[index] = 'wumpus'

# Gold 배치: Wumpus, Pit이 없는 곳 중 한 칸
safe_indices = [i for i in range(GRID_SIZE * GRID_SIZE) if grid[i] == 'empty' and i != 25]
if safe_indices:
    gold_index = random.choice(safe_indices)
    grid[gold_index] = 'gold'

'''
grid[20] = 'pit'
grid[19] = 'pit'
grid[26] = 'wumpus'
grid[28] = 'wumpus'
grid[8] = 'gold'
'''