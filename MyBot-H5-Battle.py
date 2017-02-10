import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random
import math
import time
import sys
import operator

myID, game_map = hlt.get_init()
hlt.send_init("MyBot5")

rev = {}
rev[NORTH] = SOUTH
rev[SOUTH] = NORTH
rev[EAST] = WEST
rev[WEST] = EAST
fsock=open("log.txt","w")
sys.stderr=fsock
dir2=[[0,1,3],[3,7,10],[10,11,8],[1,8,4]]
dir3=[[0,3,4,1],[3,7,10,4],[4,10,11,8],[1,4,8,4]]
dir1=[2,6,9,5] #N E S W
d2=[0,7,11,4]
d3=[0,3,7,10,11,8,4,1]
dir_dia=[1,3,10,8]#NW NE SE SW
Pat=[0, 0, 0, 0]
strength_max=[0, 0, 0, 0]
strength_min=[0, 0, 0, 0]
dic_strength = {}
width=game_map.width
height=game_map.height
turns=math.sqrt(width*height)
dic_e={}
dic_s={}
max_d=(game_map.width+ game_map.height) / 2
dis1={}
dis2={}
def find_nearest_enemy_direction(square):
    direction = NORTH
    max_distance = min(game_map.width, game_map.height) / 2
    st = 1000
    for d in (NORTH, EAST, SOUTH, WEST):
        distance = 0
        current = square
        while current.owner == myID and distance <= max_distance:
            distance += 1
            current = game_map.get_target(current, d)
        if distance < max_distance:
            direction = d
            max_distance = distance
            st=target_strength(square,d)
        elif distance == max_distance and target_strength(square,d)<st:
            direction = d
            max_distance = distance
            st=target_strength(square,d)
    return direction

def heuristic(square,direction):
    a=((0, -1), (1, 0), (0, 1), (-1, 0))
    dx, dy = a[direction]
    xo = square.x
    yo = square.y
    neighbors = [[] for i in range(6)]
    for i in range(3):
        for j in range(-i-1, i + 2):
            x = dx * (i) + j * dy
            y = dy * (i) + j * dx
            dis = abs(x) + abs(y)
            neighbors[dis].append(game_map.contents[(yo + y) % height][(xo + x) % width])


    if any(ne.owner not in (myID,0) for ne in neighbors[1]):
        self=game_map.get_target(square,rev[direction])
        prod_sum=sum(nei.production-ave_prod[myID] for i in range(3) for nei in neighbors[i] if nei.owner!=myID)
        strength_sum = sum(nei.strength/math.pow(2, i+1) for i in range(3) for nei in neighbors[i] if nei.owner != myID)
        if self.strength<min(strength_sum+square.strength,255) or prod_sum<0:
            return -100,1
        else:
            return sum(min(neighbor.strength,self.strength) for neighbor in game_map.neighbors(square) if neighbor.owner not in (0, myID)),1
    elif square.owner == 0 and square.strength> 0:
        th=square.production/square.strength
        sum_pro = list(
            nei.production / max(nei.strength, 10) * math.pow(0.5, i) for i in range(5) for nei in neighbors[i] if
            nei.owner != myID)
        #denom=[sum(x) for x in zip(*sum_pro)]
        return sum(sum_pro),0
    elif square.owner == 0:
        a = sum(neighbor.strength for neighbor in game_map.neighbors(square) if neighbor.owner not in (0, myID))
        if a==0:
            return square.production,0
        else:
            return a,0
    else:
        # return total potential damage caused by overkill when attacking this square
        return sum(neighbor.strength for neighbor in game_map.neighbors(square) if neighbor.owner not in (0,  myID)),1

def goto_battle(square):
    direction = STILL
    s=None
    if len(dis1) > 0:
        d2t, t = min(((game_map.get_distance(square, t), t) for t in dis1 if 1< game_map.get_distance(square, t) <=max_d and dis1[t]+square.strength<=260), default=(max_d, None), key=lambda t: t[0])
        if t is not None:
            m_group = list(
                (game_map.get_target(square, i),i) for i in range(4) if game_map.get_target(square, i).owner == myID)
            s, direction = min(((m, m[1]) for m in m_group if game_map.get_distance(t, m[0]) < d2t), default=(None, 5),
                               key=lambda t: square.strength)
    else:
        s = None
        direction = STILL
    return s,direction

def target_strength(square, direction):
    target = game_map.get_target(square, direction)
    coor=(target.x,target.y)
    if coor not in dic_strength:
        dic_strength[coor]=target.strength*(target.owner==myID)*(target not in dic or dic[target]==STILL)
    return square.strength + dic_strength[coor]

def update_strength(square,direction):
    self=(square.x,square.y)
    if direction==STILL:
        if self not in dic_strength:
            dic_strength[self] =min(square.strength + square.production, 255)*(square.owner==myID)-square.strength *(square.owner!=myID)
    else:
        if self not in dic_strength:
            dic_strength[self] = 0
        else:
            dic_strength[self]-=square.strength
        target=game_map.get_target(square, direction)
        coor = (target.x, target.y)
        if coor in dic_strength:
            dic_strength[coor] +=square.strength
        else:
            dic_strength[coor] = square.strength+(target.owner==myID)*target.strength

def update_map(square):
    if square.owner not in st_map:
        st_map[square.owner]=square.strength
        prod_map[square.owner]=square.production
        count_map[square.owner]=1
    else:
        st_map[square.owner]+=square.strength
        prod_map[square.owner]+=square.production
        count_map[square.owner]+=1

def get_move(square):
    global dic_e, c, e,p,pe, st_s, st_e,tn
    update_map(square)
    if square.owner not in (myID, 0):
        update_strength(square, STILL)
        if square.owner not in dic_e:
            dic_e[square.owner] = (square, None, max_d)
        else:
            enemy, self, distance = dic_e[square.owner]
            if self is not None:
                dis = game_map.get_distance(square, self)
                if dis < distance:
                    dic_e[square.owner] = (square, self, dis)
    elif square.owner == myID:
        for key in dic_e:
            target, self, distance = dic_e[key]
            dis = game_map.get_distance(square, target)
            if dis < distance:
                distance = dis
                dic_e[key] = (target, square, distance)
        neighbors = [neighbor for neighbor in game_map.neighbors(square, 2)]
        enemy_e = any(neighbors[k].owner not in (0,myID) for k in dir1)  # find out if there is enemy in distance<=2

        if any(ne.owner==0 for ne in neighbors):
            target, direction,sc = max(
                ((neighbor, direction, heuristic(neighbor,direction)) for direction, neighbor in enumerate(game_map.neighbors(square)) if
                 neighbor.owner != myID), default=(None, STILL,(-100,0)), key=lambda t: t[3][0])
            score = sc[0]
            ind=sc[1]
            st=1000
            if target is not None:
                if target.strength >= square.strength or target_strength(square, direction) >= 280:
                    direction = STILL
                for i in (NORTH, EAST, SOUTH, WEST):
                    t1 = neighbors[dir1[i]]
                    if t1.owner == myID:
                        t2, direction2 = max(((neighbors[dir3[i][k]], k) for k in range(4) if neighbors[dir3[i][k]].owner != myID and k!=rev[i]),
                                    default=(None, None), key=lambda t: heuristic(t[0],t[1]))
                        if t2 is not None and (t1.strength + t1.production) <= t2.strength :
                            eva,ind2 = heuristic(t2,direction2)
                            if eva > score and target_strength(square,i) <= 280:
                                score = eva
                                t2s = t2
                                t1s = t1
                                direction = i if t2s.strength < t1s.strength + t1s.production + square.strength else STILL
            else:
                for i in (NORTH, EAST, SOUTH, WEST):
                    #t2, _ = max(((neighbors[k], k) for k in dir2[i] if neighbors[k].owner != myID),default=(None, None), key=lambda t: heuristic(t[0]))
                    t2= sum((heuristic(neighbors[dir3[i][k]],k)+0.01) for k in range(4) if neighbors[dir3[i][k]].owner != myID and k!=rev[i])/(sum(1 for k in range(4) if neighbors[dir3[i][k]].owner!= myID and k!=rev[i])+0.01)
                    eva = t2
                    if eva >= score and target_strength(square,i)<280:
                        score=eva
                        direction=i if square.strength > 5*square.production else STILL
            dic[square]=direction
            update_strength(square,direction)
            return
        elif square.strength < square.production * 5:
             dic[square]= STILL
             update_strength(square, STILL)
             return

        border = any(neighbor.owner != myID for neighbor in game_map.neighbors(square))
        if not border:
             direction=find_nearest_enemy_direction(square)
             dic[square]= direction
             update_strength(square, direction)
        else:
            #wait until we are strong enough to attack
             dic[square]= STILL
             update_strength(square, STILL)
        return
tn=0
st_map = {}
prod_map = {}
count_map = {}
while True:
    game_map.get_frame()
    n_boarder=0
    moves=[]
    dic = {}

    for square in game_map:
        if square not in dic:
            get_move(square)
    for key in dic:
        c = c + 1
        p+=key.production
        st_s += key.strength
        if key.strength < key.production*3:
            moves.append(Move(key,STILL))
        else:
            moves.append(Move(key, dic[key]))
    del dis1[:]
    dis1 = dis2
    fsock.write(str(len(dis2)) + "\n")
    fsock.flush()
    dis2 = {}
    ave_prod = {key : prod_map[key] / (max(count_map[key], 1)) for key in prod_map}
    dic_strength = {}
    st_map = {}
    prod_map = {}
    count_map = {}

    hlt.send_frame(moves)

