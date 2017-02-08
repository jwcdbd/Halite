import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random
import math
import time
import sys


myID, game_map = hlt.get_init()
hlt.send_init("Battle")

rev = {}
rev[NORTH] = SOUTH
rev[SOUTH] = NORTH
rev[EAST] = WEST
rev[WEST] = EAST
fsock=open("log.txt","w")
sys.stderr=fsock
dir2=[[0,1,3],[3,7,10],[10,11,8],[1,8,4]]
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
dis1 = []
dis2 = []
max_d=(game_map.width+ game_map.height)/2

def goto_battle(square):
    direction = STILL
    s=None
    if len(dis1) > 0:
        d2t, t = min(((game_map.get_distance(square, t), t) for t in dis1 if 1< game_map.get_distance(square, t) <=5), default=(max_d, None), key=lambda t: t[0])
        if t is not None:
            m_group = list(
                (game_map.get_target(square, i),i) for i in range(4) if game_map.get_target(square, i).owner == myID)
            s, direction = min(((m, m[1]) for m in m_group if game_map.get_distance(t, m[0]) < d2t), default=(None, 5),
                               key=lambda t: target_strength(square,t[1]))
    else:
        s = None
        direction = STILL
    return s,direction

def find_nearest_enemy_direction(square):
    direction = NORTH
    max_distance = min(game_map.width, game_map.height) / 2
    for d in (NORTH, EAST, SOUTH, WEST):
        distance = 0
        current = square
        while current.owner == myID and distance < max_distance:
            distance += 1
            current = game_map.get_target(current, d)
        if distance < max_distance:
            direction = d
            max_distance = distance
    return direction

def heuristic(square):
    neighbors = list(game_map.neighbors(square, 1))
    sum_pro=sum(ne.production for ne in neighbors if ne.owner==0)
    sum_str=sum(ne.strength for ne in neighbors if ne.owner==0)
    if square.owner == 0 and square.strength*sum_str > 0:
        return square.production / square.strength+sum_pro/sum_str*0.6
    elif square.owner == 0 :
        a=sum(neighbor.strength for neighbor in game_map.neighbors(square) if neighbor.owner not in (0, myID))
        if a==0:
            return square.production+sum_pro
        else:
            return a
    else:
        # return total potential damage caused by overkill when attacking this square
        return sum(neighbor.strength for neighbor in game_map.neighbors(square) if neighbor.owner not in (0,  myID))

def get_damage(square):  # find out the damage could make if the square move or still
    neighbors = [neighbor for neighbor in game_map.neighbors(square, 2)]
    enemy_e = any(ne.owner not in (0, myID) for ne in neighbors)  # find out if there is enemy in distance<=2
    Dr = 0  ## return damage
    direction = STILL
    if enemy_e and (square not in dic or dic[square] == STILL):
        D_s = min(square.strength + square.production + sum(
            neighbors[k].strength for k in dir1 if neighbors[k].owner == myID), 255)
        Dr = sum(min(D_s, neighbors[k].strength) for k in dir1 if neighbors[k].owner not in (0, myID)) * 0.7 + sum(
            min(D_s, neighbors[k].strength) for k in dir_dia if neighbors[k].owner not in (0, myID)) * 0.3 + sum(
            min(D_s, neighbors[k].strength) for k in d2 if neighbors[k].owner not in (0, myID)) * 0.3
        for i in (NORTH, EAST, SOUTH, WEST):
            target = neighbors[dir1[i]]
            neighbors2 = [neighbor for neighbor in game_map.neighbors(target, 2)]
            D = min(square.strength + neighbors2[i].strength * (neighbors2[i].owner in (myID, 0)) + sum(
                neighbors2[k].strength for k in dir2[i] if neighbors2[k].owner == myID), 255)
            Dtotal = min(D, target.strength * (target.owner not in (myID, 0))) + sum(
                min(D, neighbors2[k].strength) for k in dir1 if neighbors2[k].owner not in (0, myID)) * 0.7 + sum(
                min(D, neighbors2[k].strength) for k in d2 if neighbors2[k].owner not in (0, myID)) * 0.3 + sum(
                min(D, neighbors2[k].strength) for k in dir_dia if
                neighbors2[k].owner not in (0, myID)) * 0.3 - target.strength * (target.owner == 0)
            if Dtotal > Dr:
                Dr = Dtotal
                direction = i
        return Dr, direction, square
    else:
        return 0, STILL, square
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

def get_move(square,dis2):
    global dic_e, c, e,p,pe, st_s, st_e,tn
    if square.owner not in (myID, 0):
        e = e + 1
        pe+=square.production
        st_e += square.strength
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
        neighbors = list(game_map.neighbors(square, 2))
        enemy_e = [neighbors[k] for k in d3 if neighbors[k].owner not in (0,myID)] # find out if there is enemy in distance<=2
        if any(neighbors[k].owner ==0 for k in dir1):
            #target, direction = goto_battle(square)
            target=None
            if target is None:
                target, direction = max(
                    ((neighbor, direction) for direction, neighbor in enumerate(game_map.neighbors(square)) if
                     neighbor.owner != myID), default=(None, STILL), key=lambda t: heuristic(t[0]))
                score =  -100
                if target is not None:
                    score= heuristic(target)
                    if target.strength >= square.strength:
                        direction=STILL
                t2s=None
                t1s=None
                for i in (NORTH, EAST, SOUTH, WEST):
                    t1 = neighbors[dir1[i]]
                    if t1.owner==myID:
                        t2, _ = max(((neighbors[k], k) for k in dir2[i] if neighbors[k].owner != myID), default = (None, None), key = lambda t: heuristic(t[0]))
                        if t2 is not None and (t1.strength+t1.production)<= t2.strength:
                            eva =heuristic(t2)
                            if eva > score:
                                score=eva
                                t2s=t2
                                t1s=t1
                                direction=i if t2s.strength<t1s.strength+t1s.production+square.strength else STILL
            dic[square]=direction
            update_strength(square, direction)
            if len(enemy_e)>0 and game_map.get_target(square,direction).owner!=myID:
                dis2.append(game_map.get_target(square,direction))
            return
        elif square.strength < square.production * 5:
             dic[square]= STILL
             update_strength(square, STILL)
             return 
        border = any(neighbor.owner != myID for neighbor in game_map.neighbors(square))
        if not border:
             target,direction = goto_battle(square)
             if target is None:
                 direction= find_nearest_enemy_direction(square)
             dic[square]=direction
             update_strength(square, STILL)
        else:
            #wait until we are strong enough to attack
             dic[square]= STILL
             update_strength(square, STILL)
        return
tn=0
while True:
    game_map.get_frame()
    p=0
    pe=0
    c = 0
    e = 0
    st_s = 0
    st_e = 0
    n_boarder=0
    moves=[]
    dic = {}
    for square in game_map:
        if square not in dic:
            get_move(square,dis2)
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
    fsock.write(str(len(dis2))+"\n")
    fsock.flush()
    dis2 = []
    dic_strength = {}
    hlt.send_frame(moves)
fsock.close()
