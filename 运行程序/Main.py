import pygame
from major import *
import os
import socket
import threading
import queue
import time

# 获取当前文件路径
base_dir = os.path.abspath(os.path.dirname(__file__)) 
# 拼接资源所在路径
base_dir = os.path.join(base_dir, "resources")
# 背景音乐路径
music_path = os.path.join(base_dir, "music", "music.ogg")
# 屏幕长宽
SCR_WIDTH = 300
SCR_HEIGHT = 210
# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
SKYBLUE = (135,206,250)
ORANGE = (238,154,73)
YELLOW = (255,255,0)
# 初始化pygame
pygame.init()
pygame.mixer.init()
# 加载背景音乐
pygame.mixer.music.load(music_path)
pygame.mixer.music.play(-1)  # 无限循环播放
# 设置字体
data_path = os.path.join(base_dir, "language", "msyh.ttc") 
try:
    font = pygame.font.Font(data_path, 24)
except:
    print("字体加载失败")
    exit()
# 设置屏幕
screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
pygame.display.set_caption("五子棋")
# 初始化数据
over_pos = []    # 已落子位置
win_count = [0, 0]   # 白棋胜利数，黑棋胜利数
page = 1    # 页面状态
game_page = (("请选择游戏模式", "人机对战", "玩家对战"),
            ("请选择：", "玩家先手", "电脑先手"),
            ("游戏结束是否继续", "重新开始", "退出游戏"),
            ("请选择：", "本地模式", "网络模式"),
            ("网络对战模式", "创建房间", "加入房间")
            )
flag = True   # 是否切换页面大小
music_on = True   # 背景音乐开关

# 网络相关变量
network_client = None
network_queue = queue.Queue()
player_role = 0  # 1: 黑方(房主), 2: 白方(加入者)
room_id = ""
game_started = False
waiting_text = "等待玩家加入..."
connection_status = "未连接"

# 绘制开始和结束页面
def draw_page(game_page, x, y):
    screen.fill(ORANGE)
    text = font.render(f"{game_page[0]}", True, BLACK)
    screen.blit(text, (SCR_WIDTH//2-text.get_width()//2, 30))

    #第一个按钮
    pygame.draw.rect(screen, SKYBLUE, (20, 80, 120, 50))
    text_one = font.render(f"{game_page[1]}", True, BLACK)
    screen.blit(text_one, (30, 90))
    #第二个按钮
    pygame.draw.rect(screen, SKYBLUE, (160, 80, 120, 50))
    text_two = font.render(f"{game_page[2]}", True, BLACK)
    screen.blit(text_two, (170, 90))
    # 绘制光标
    if 20 <= x <= 140 and 80 <= y <= 130:
        pygame.draw.rect(screen, RED, (20, 80, 120, 50), 2 , 1)
    elif 160 <= x <= 280 and 80 <= y <= 130:
        pygame.draw.rect(screen, RED, (160, 80, 120, 50),2 , 1)
    pygame.display.update()

# 绘制游戏棋盘
def refresh_board(over_pos):
    # 绘制棋盘
    pygame.display.set_caption("五子棋")
    screen.fill(ORANGE)
    for i in range(27,670,44):
        if i == 27 or i == 643:
            pygame.draw.line(screen, BLACK, (i,27), (i,643), 4)
            pygame.draw.line(screen, BLACK, (27,i), (643,i), 4)
        else:
            pygame.draw.line(screen, BLACK, (i,27), (i,643), 2)
            pygame.draw.line(screen, BLACK, (27,i), (643,i), 2)
    pygame.draw.circle(screen, BLACK, (335,335), 8, 0)
    pygame.draw.circle(screen, BLACK, (159,159), 8, 0)
    pygame.draw.circle(screen, BLACK, (511,159), 8, 0)
    pygame.draw.circle(screen, BLACK, (159,511), 8, 0)
    pygame.draw.circle(screen, BLACK, (511,511), 8, 0)
    # 绘制棋子
    for val in over_pos:
        pygame.draw.circle(screen, val[1], val[0], 20, 0)
    # 显示信息
    text = font.render("当前执子:", True, BLACK)
    screen.blit(text, (655, 130))
    if len(over_pos)%2 == 0:
        pygame.draw.circle(screen, BLACK, (780, 150), 15, 0)
    else:
        pygame.draw.circle(screen, WHITE, (780, 150), 15, 0)
    if over_pos:  # 确保列表不为空
        last_pos = over_pos[-1][0]  # 取出坐标 [x, y]
        x, y = last_pos
        pygame.draw.rect(screen, YELLOW, (x - 22, y - 22, 44, 44), 2)

    text_count = font.render("当前已胜局数：", True, BLACK)
    screen.blit(text_count, (655, 450))
    text_black = font.render(f"黑棋：{win_count[1]}", True, BLACK)
    screen.blit(text_black, (655, 480))
    text_white = font.render(f"白棋：{win_count[0]}", True, BLACK)
    screen.blit(text_white, (655, 510))
    
    # 显示网络状态
    if player_role > 0:
        role_text = "黑方" if player_role == 1 else "白方"
        status_text = font.render(f"网络状态: {connection_status}", True, RED)
        role_text_display = font.render(f"你的身份: {role_text}", True, RED)
        screen.blit(status_text, (655, 300))
        screen.blit(role_text_display, (655, 330))

# 处理事件
def handle_events(button_actions):
    global music_on
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            for rect, action in button_actions:
                if rect.collidepoint(x, y):
                    action()
                    pygame.time.delay(200)
                    break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                if music_on:
                    pygame.mixer.music.pause()
                    music_on = False
                else:
                    pygame.mixer.music.unpause()
                    music_on = True
    return True

# 结束页面
def page_0():
    global screen, flag, page, running
    if not flag:
        screen = pygame.display.set_mode((300, 210))
        flag = True
    draw_page(game_page[2], *pygame.mouse.get_pos())
    button_actions = [
        (pygame.Rect(20, 80, 120, 50), lambda: change_page(1)),
        (pygame.Rect(160, 80, 120, 50), lambda: quit_game()),
    ]
    return handle_events(button_actions)

# 选择人机或者玩家对战页面
def page_1():
    draw_page(game_page[0], *pygame.mouse.get_pos())
    button_actions = [
        (pygame.Rect(20, 80, 120, 50), lambda: change_page(2)),
        (pygame.Rect(160, 80, 120, 50), lambda: change_page(6)),
    ]
    return handle_events(button_actions)

# 人机对战选择先手页面
def page_2():
    draw_page(game_page[1], *pygame.mouse.get_pos())
    button_actions = [
        (pygame.Rect(20, 80, 120, 50), lambda: change_page(4)),
        (pygame.Rect(160, 80, 120, 50), lambda: change_page(5)),
    ]
    return handle_events(button_actions)

# 本地玩家对战页面
def page_3():
    global over_pos, page, win_count, flag, screen, music_on
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = find_pos(*event.pos)
            if check_over_pos(x, y, over_pos):
                color = BLACK if len(over_pos) % 2 == 0 else WHITE
                over_pos.append([[x, y], color])
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                if music_on:
                    pygame.mixer.music.pause()
                    music_on = False
                else:
                    pygame.mixer.music.unpause()
                    music_on = True
    refresh_board(over_pos)
    res = check_number(over_pos, 5)
    if res[0] != 0:
        for pos in res[1]:
            pygame.draw.rect(screen, RED, (pos[0]*44+5, pos[1]*44+5, 44, 44), 2)
        msg = font.render("白棋获胜！" if res[0] == 1 else "黑棋获胜！", True, RED)
        screen.blit(msg, (655, 200))
        text = font.render("点击任意区域继续", True, RED)
        screen.blit(text, (655, 250))
        pygame.display.update()
        win_count[res[0] - 1] += 1
        over_pos = []
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        page = 0
        return True
    if flag:
        screen = pygame.display.set_mode((870, 670))
        flag = False
    x, y = find_pos(*pygame.mouse.get_pos())
    if check_over_pos(x, y, over_pos):
        pygame.draw.rect(screen, SKYBLUE, (x-22, y-22, 44, 44), 2)
    pygame.display.update()
    return True

# 人机对战页面
def page_4_5():
    global over_pos, page, win_count, flag, screen, music_on
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = find_pos(*event.pos)
            if check_over_pos(x, y, over_pos):
                color = BLACK if len(over_pos) % 2 == 0 else WHITE
                over_pos.append([[x, y], color])
                self_color = 1 if page == 4 else 2
                self = WHITE if page == 4 else BLACK
                num1, num2 = find_pc_pos(over_pos, self_color)
                over_pos.append([[num1*44+27, num2*44+27], self])
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                if music_on:
                    pygame.mixer.music.pause()
                    music_on = False
                else:
                    pygame.mixer.music.unpause()
                    music_on = True
    refresh_board(over_pos)
    res = check_number(over_pos, 5)
    if res[0] != 0:
        for pos in res[1]:
            pygame.draw.rect(screen, RED, (pos[0]*44+5, pos[1]*44+5, 44, 44), 2)
        msg = font.render(
            "电脑获胜！" if (res[0] == 1 and page == 4) or (res[0] == 2 and page == 5)
            else "玩家获胜！", True, RED
        )
        screen.blit(msg, (655, 200))
        text = font.render("点击任意区域继续", True, RED)
        screen.blit(text, (655, 250))
        pygame.display.update()
        win_count[res[0] - 1] += 1
        over_pos = []
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        page = 0
        return True
    if flag:
        screen = pygame.display.set_mode((870, 670))
        flag = False
        if page == 5:
            over_pos.append([[335, 335], BLACK])
    x, y = find_pos(*pygame.mouse.get_pos())
    if check_over_pos(x, y, over_pos):
        pygame.draw.rect(screen, SKYBLUE, (x-22, y-22, 44, 44), 2)
    pygame.display.update()
    return True

# 选择本地对战或者网络匹配页面
def page_6():
    draw_page(game_page[3], *pygame.mouse.get_pos())
    button_actions = [
        (pygame.Rect(20, 80, 120, 50), lambda: change_page(3)),
        (pygame.Rect(160, 80, 120, 50), lambda: change_page(7)),
    ]
    return handle_events(button_actions)

# 创建房间或者加入房间页面
def page_7():
    global page
    draw_page(game_page[4], *pygame.mouse.get_pos())
    button_actions = [
        (pygame.Rect(20, 80, 120, 50), lambda: create_room()),
        (pygame.Rect(160, 80, 120, 50), lambda: join_room()),
    ]
    return handle_events(button_actions)

# 创建房间
def create_room():
    global network_client, player_role, connection_status, page, waiting_text
    try:
        # 连接到服务器
        network_client = socket.socket()
        network_client.connect(('localhost', 8800))
        connection_status = "已连接(房主)"
        player_role = 1  # 房主为黑方
        waiting_text = "等待其他玩家加入..."
        
        # 启动接收线程
        threading.Thread(target=recv_loop, daemon=True).start()
        page = 8  # 进入等待页面
    except Exception as e:
        print("连接服务器失败:", e)
        connection_status = f"连接失败: {str(e)}"

# 加入房间
def join_room():
    global network_client, player_role, connection_status, page
    try:
        # 连接到服务器
        network_client = socket.socket()
        network_client.connect(('localhost', 8800))
        connection_status = "已连接(玩家)"
        player_role = 2  # 加入者为白方
        page = 8  # 进入等待页面
        
        # 启动接收线程
        threading.Thread(target=recv_loop, daemon=True).start()
    except Exception as e:
        print("连接服务器失败:", e)
        connection_status = f"连接失败: {str(e)}"

# 接收网络消息的循环
def recv_loop():
    global network_queue, game_started, connection_status, over_pos, player_role
    
    # 首先接收玩家角色
    try:
        role_data = network_client.recv(1024).decode("utf-8")
        if role_data == "1" or role_data == "2":
            player_role = int(role_data)
            connection_status = f"已连接(玩家{player_role})"
            print(f"分配角色: {player_role}")
        else:
            connection_status = "角色分配失败"
    except Exception as e:
        print("接收角色失败:", e)
        connection_status = f"连接错误: {str(e)}"
        return
    
    while True:
        try:
            data = network_client.recv(1024).decode("utf-8")
            if not data:
                break
                
            if data == "start":
                print("收到游戏开始消息")
                network_queue.put(("start", None))
                continue
                
            # 处理棋子位置消息
            parts = data.split(',')
            if len(parts) == 2:
                x, y = map(int, parts)
                print(f"收到落子位置: ({x}, {y})")
                network_queue.put(("move", (x, y)))
                
        except Exception as e:
            print("接收数据出错:", e)
            connection_status = f"连接错误: {str(e)}"
            break

# 网络对战等待页面
def page_8():
    global page, game_started, flag, screen, connection_status, player_role
    
    # 检查网络队列中的消息
    while not network_queue.empty():
        event_type, data = network_queue.get()
        if event_type == "start":
            game_started = True
            connection_status = "游戏开始!"
            print("收到游戏开始消息")
    
    # 如果游戏开始，跳转到游戏页面
    if game_started:
        if flag:
            screen = pygame.display.set_mode((870, 670))
            flag = False
        page = 9  # 进入游戏页面
        return True
    
    # 绘制等待界面
    screen.fill(ORANGE)
    title = font.render("网络对战", True, BLACK)
    screen.blit(title, (SCR_WIDTH//2 - title.get_width()//2, 30))
    
    status = font.render(connection_status, True, RED)
    screen.blit(status, (SCR_WIDTH//2 - status.get_width()//2, 70))
    
    if player_role == 1:
        role_text = font.render("你的身份: 黑方(房主)", True, BLACK)
    else:
        role_text = font.render("你的身份: 白方(玩家)", True, BLACK)
    screen.blit(role_text, (SCR_WIDTH//2 - role_text.get_width()//2, 100))
    
    waiting = font.render(waiting_text, True, BLACK)
    screen.blit(waiting, (SCR_WIDTH//2 - waiting.get_width()//2, 130))
    
    # 返回按钮
    pygame.draw.rect(screen, SKYBLUE, (100, 160, 100, 40))
    back_text = font.render("返回", True, BLACK)
    screen.blit(back_text, (140 - back_text.get_width()//2, 170))
    
    pygame.display.update()
    
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if 100 <= x <= 200 and 160 <= y <= 200:
                # 关闭网络连接
                if network_client:
                    try:
                        network_client.close()
                    except:
                        pass
                page = 1  # 返回主菜单
                return True
    
    return True

# 网络对战游戏页面
def page_9():
    global over_pos, page, win_count, running, player_role
    
    # 处理网络队列中的消息
    while not network_queue.empty():
        event_type, data = network_queue.get()
        if event_type == "start":
            game_started = True
            connection_status = "游戏开始!"
        elif event_type == "move":
            x, y = data
            screen_x = x * 44 + 27
            screen_y = y * 44 + 27
            
            # 确定棋子颜色
            color = BLACK if player_role == 2 else WHITE
            over_pos.append([[screen_x, screen_y], color])
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 只有轮到当前玩家才能落子
            current_turn = len(over_pos) % 2
            if (player_role == 1 and current_turn == 0) or (player_role == 2 and current_turn == 1):
                x, y = find_pos(*event.pos)
                if check_over_pos(x, y, over_pos):
                    # 确定棋子颜色
                    color = BLACK if len(over_pos) % 2 == 0 else WHITE
                    over_pos.append([[x, y], color])
                    
                    # 发送棋子位置给对手
                    board_x = (x - 27) // 44
                    board_y = (y - 27) // 44
                    try:
                        network_client.send(f"{board_x},{board_y}".encode("utf-8"))
                    except Exception as e:
                        print("发送数据出错:", e)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                global music_on
                if music_on:
                    pygame.mixer.music.pause()
                    music_on = False
                else:
                    pygame.mixer.music.unpause()
                    music_on = True
    
    refresh_board(over_pos)
    
    # 显示当前状态
    current_turn = len(over_pos) % 2
    if (player_role == 1 and current_turn == 0) or (player_role == 2 and current_turn == 1):
        status_text = "轮到你落子"
    else:
        status_text = "等待对手落子..."
    turn_text = font.render(status_text, True, RED)
    screen.blit(turn_text, (655, 200))
    
    # 判断输赢
    res = check_number(over_pos, 5)
    if res[0] != 0:
        for pos in res[1]:
            pygame.draw.rect(screen, RED, (pos[0]*44+5, pos[1]*44+5, 44, 44), 2)
        winner = "黑棋" if res[0] == 2 else "白棋"
        msg = font.render(f"{winner}获胜！", True, RED)
        screen.blit(msg, (655, 230))
        text = font.render("点击任意区域继续", True, RED)
        screen.blit(text, (655, 260))
        pygame.display.update()
        
        # 记录胜局
        if res[0] == 2:  # 黑棋赢
            win_count[1] += 1
        else:  # 白棋赢
            win_count[0] += 1
        
        # 等待点击
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
        
        # 重置游戏
        over_pos = []
        game_started = False
        page = 0  # 回到结束页面
        
        # 关闭网络连接
        if network_client:
            try:
                network_client.close()
            except:
                pass
        return True
    
    pygame.display.update()
    return True

# 切换页面
def change_page(p):
    global page
    page = p

# 退出游戏
def quit_game():
    global running
    running = False

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

# 游戏主循环
running = True
while running:
    if page == 0:
        running = page_0()    # 结束页面
    elif page == 1: 
        running = page_1()    # 选择人机或者玩家对战页面
    elif page == 2:
        running = page_2()    # 人机对战选择先手页面
    elif page == 3:
        running = page_3()    # 本地玩家对战页面
    elif page in (4, 5):
        running = page_4_5()  # 人机对战页面
    elif page == 6:
        running = page_6()    # 选择本地对战或者网络匹配页面
    elif page == 7:
        running = page_7()    # 网络匹配页面
    elif page == 8:
        running = page_8()    # 网络对战等待页面
    elif page == 9:
        running = page_9()    # 网络对战游戏页面

pygame.quit()
exit()