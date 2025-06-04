import socket
import threading
import sys

clients = []  # 存储客户端连接
game_rooms = {}  # 存储游戏房间（这里简化处理，只支持一个房间）

def handle_client(conn, player_id):
    global game_rooms
    room_id = "default_room"  # 简化处理，只使用一个房间
    
    while True:
        try:
            data = conn.recv(1024).decode("utf-8")
            if not data:
                break
                
            print(f"玩家{player_id}发送数据: {data}")
            
            # 转发数据给对手
            if room_id in game_rooms:
                for client in game_rooms[room_id]:
                    if client != conn:
                        try:
                            client.send(data.encode("utf-8"))
                            print(f"向玩家发送数据: {data}")
                        except:
                            # 如果发送失败，可能是对手已断开
                            print(f"向玩家发送数据失败: {player_id}")
        except Exception as e:
            print(f"处理玩家{player_id}时出错: {e}")
            break
    
    # 玩家断开连接
    print(f"玩家{player_id}断开连接")
    if room_id in game_rooms and conn in game_rooms[room_id]:
        game_rooms[room_id].remove(conn)
        if not game_rooms[room_id]:
            del game_rooms[room_id]
            print(f"房间{room_id}已关闭")

def start_server():
    server = socket.socket()
    server.bind(('0.0.0.0', 8800))
    server.listen(5)  # 允许更多连接
    print("服务器已启动，等待玩家连接...")
    
    while True:
        conn, addr = server.accept()
        print(f"新连接来自: {addr}")
        
        room_id = "default_room"  # 简化处理，只使用一个房间
        
        # 如果房间不存在，创建新房间
        if room_id not in game_rooms:
            game_rooms[room_id] = []
        
        # 分配玩家角色
        player_id = len(game_rooms[room_id]) + 1
        
        # 发送玩家角色
        try:
            conn.send(str(player_id).encode("utf-8"))
            print(f"发送玩家角色: {player_id}")
        except:
            print("发送玩家角色失败")
            conn.close()
            continue
        
        # 将玩家加入房间
        game_rooms[room_id].append(conn)
        print(f"玩家{player_id}加入房间{room_id}")
        
        # 当房间满2人时通知游戏开始
        if len(game_rooms[room_id]) == 2:
            print(f"房间{room_id}已满，游戏开始！")
            for client in game_rooms[room_id]:
                try:
                    client.send("start".encode("utf-8"))
                    print("发送游戏开始消息")
                except:
                    print("发送开始消息失败")
        
        # 启动线程处理客户端
        threading.Thread(target=handle_client, args=(conn, player_id), daemon=True).start()

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n服务器已关闭")
        sys.exit(0)