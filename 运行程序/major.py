import numpy as np
import copy
WHITE = (255, 255, 255)
# 寻找目标数量为num_text的数字
DIRECTIONS = [(0,1), (1,0), (1,1), (1,-1)]
def check_number(over_pos, num_text):
    mp = np.zeros((15,15), dtype=int)
    for val in over_pos:
        x = int((val[0][0]-27)//44)
        y = int((val[0][1]-27)//44)
        mp[x][y] = 1 if val[1] == WHITE else 2

    def check_line(start_x, start_y, dx, dy):
        x, y = start_x, start_y
        pos1, pos2 = [], []
        for _ in range(15):
            if 0 <= x < 15 and 0 <= y < 15:
                if mp[x][y] == 1:
                    pos1.append([x, y])
                    pos2 = []
                elif mp[x][y] == 2:
                    pos2.append([x, y])
                    pos1 = []
                else:
                    pos1 = []
                    pos2 = []
                if len(pos1) == num_text:
                    return [1, pos1]
                if len(pos2) == num_text:
                    return [2, pos2]
            x += dx
            y += dy
        return [0, []]

    # 遍历所有起点和方向
    for i in range(15):
        for j in range(15):
            for dx, dy in DIRECTIONS:
                # 检查该方向是否有足够空间
                end_x = i + dx * (num_text - 1)
                end_y = j + dy * (num_text - 1)
                if 0 <= end_x < 15 and 0 <= end_y < 15:
                    result = check_line(i, j, dx, dy)
                    if result[0] != 0:
                        return result

    return [0, []]
# 检测是否可以落子
def check_over_pos(x,y,over_pos):
    for val in over_pos:
        if val[0][0] == x and val[0][1] == y:
            return False
    return True
# 找到落子位置
def find_pos(x,y):
    for i in range(27,670,44):
        for j in range(27,670,44):
            if x >= i - 22 and x <= i + 22 and y >= j - 22 and y <= j + 22:
                return (i,j)
    return x, y
# 找到电脑落子位置，self为1表示找白色，为2表示找黑色
def find_pc_pos(over_pos, self_color):
    mp = np.zeros((15,15),dtype = int)
    for val in over_pos:
        x = int((val[0][0]-27)/44)
        y = int((val[0][1]-27)/44)
        if val[1] == WHITE:
            mp[x][y] = 1
        else:
            mp[x][y] = 2
    opponent_color = 1 if self_color == 2 else 2
    board_size = 15
    # 各种模式的分值（简化版）
    score_table = {
        5: 100000,   # 连五
        4: 10000,    # 活四
        3: 1000,     # 活三
        2: 100,      # 活二
        1: 10,       # 单子
    }
    # 获取某一方向的连续同色棋子数（向两个方向扩展）
    def count_line(board, x, y, dx, dy, color):
        count = 1
        # 向一个方向数
        i, j = x + dx, y + dy
        while 0 <= i < board_size and 0 <= j < board_size and board[i][j] == color:
            count += 1
            i += dx
            j += dy
        # 向另一个方向数
        i, j = x - dx, y - dy
        while 0 <= i < board_size and 0 <= j < board_size and board[i][j] == color:
            count += 1
            i -= dx
            j -= dy
        return count
    def get_score(board, x, y, color):
        if board[x][y] != 0:
            return 0
        score = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = count_line(board, x, y, dx, dy, color)
            score += score_table.get(count, 0)
        return score
    max_score = -1
    best_pos = (7, 7)  # 默认中间为首选
    for i in range(board_size):
        for j in range(board_size):
            if mp[i][j] == 0:
                score_self = get_score(mp, i, j, self_color)
                score_enemy = get_score(mp, i, j, opponent_color)
                total_score = score_self + score_enemy * 0.9  # 优先进攻，兼顾防守
                if total_score > max_score:
                    max_score = total_score
                    best_pos = (i, j)
    return best_pos