from config import GRID_SIZE, WORLD_SIZE, WUMPUS_PROB, PIT_PROB
import random

# Initialize grid
grid = ['wall'] * (GRID_SIZE * GRID_SIZE)

wumpus_count = 0
pit_count = 0

# Generate Wumpus, Pit, and Gold
for y in range(1, WORLD_SIZE + 1):
    for x in range(1, WORLD_SIZE + 1):
        grid_y = GRID_SIZE - y - 1
        index = grid_y * GRID_SIZE + x
        grid[index] = 'empty'
'''
        if index == 25 or index == 26 or index == 19:  # (1,1), (1,2), (2,1)에는 생성 X
            continue

        if pit_count < 2 and random.random() < PIT_PROB:
            grid[index] = 'pit'
            pit_count += 1
        elif wumpus_count < 2 and random.random() < WUMPUS_PROB:
            grid[index] = 'wumpus'
            wumpus_count += 1

# Gold 배치: Wumpus, Pit이 없는 곳 중 한 칸
safe_indices = [i for i in range(GRID_SIZE * GRID_SIZE) if grid[i] == 'empty' and i != 25]
if safe_indices:
    gold_index = random.choice(safe_indices)
    grid[gold_index] = 'gold'

'''
grid[13] = 'pit'
grid[27] = 'wumpus'
grid[8] = 'gold'
