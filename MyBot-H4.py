import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random
import math
import time
import sys
import operator

myID, game_map = hlt.get_init()
hlt.send_init("MyBot4")

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

    if square.owner == 0 and square.strength> 0:
        th=square.production/square.strength
        dx, dy = a[direction]
        xo = square.x
        yo = square.y
        neighbors = []
        for i in range(3):
            neighbor=[]
            for j in range(-1, 2):
                x = dx * (i-abs(j)) + j * dy
                y = dy * (i-abs(j)) + j * dx
                neighbor.append(game_map.contents[(yo + y) % height][(xo + x) % width])
            neighbors.append(neighbor)

        sum_pro = tuple((nei.production/max(nei.strength,10)/(i+1),1/(i+1)) for i in range(3) for nei in neighbors[i] if nei.owner == 0)
        denom=[sum(x) for x in zip(*sum_pro)]

        return denom[0]/denom[1]
    elif square.owner == 0:
        a = sum(neighbor.strength for neighbor in game_map.neighbors(square) if neighbor.owner not in (0, myID))
        if a==0:
            return square.production
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

def get_move(square):
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
        neighbors = [neighbor for neighbor in game_map.neighbors(square, 2)]
        enemy_e = any(neighbors[k].owner not in (0,myID) for k in dir1)  # find out if there is enemy in distance<=2
        if enemy_e:
            group=list(get_damage(neighbors[k]) for k in range(12) if neighbors[k].owner==myID)
            group.append(get_damage(square))
            Dtotal,dir,sq=max((gr for gr in group if gr[2] is not None),default=(0,5,square),key=lambda t: t[0])
            neighbors2 = [neighbor for neighbor in game_map.neighbors(sq, 2)]
            dic[sq]=dir
            update_strength(sq, dir)
            if dir==STILL:
                for k in range(4):
                    if neighbors2[dir1[k]].owner==myID and neighbors2[dir1[k]].strength < sq.strength and target_strength(neighbors2[dir1[k]],rev[k])<=270:
                        dic[neighbors2[dir1[k]]]=rev[k]
                        update_strength(neighbors2[dir1[k]],rev[k])
                    if neighbors2[dir_dia[k]].owner == myID and neighbors2[dir_dia[k]] not in dic:
                        dic[neighbors2[dir_dia[k]]]=STILL
                        update_strength(neighbors2[dir_dia[k]],STILL)
            else:
                for k in range(4):
                    if neighbors2[dir1[k]].owner==myID:
                        dic[neighbors2[dir1[k]]]=STILL
                        update_strength(neighbors2[dir1[k]], STILL)
                if neighbors2[dir_dia[dir]].owner == myID and target_strength(neighbors2[dir_dia[dir]],(dir+1)%4)<=255:
                    dic[neighbors2[dir_dia[dir]]] = (dir+1)%4
                    update_strength(neighbors2[dir_dia[dir]],(dir+1)%4)
                if neighbors2[dir_dia[(dir+1) % 4]].owner == myID and target_strength(neighbors2[dir_dia[(dir+1) % 4]],(dir+3)%4)<=255:
                    dic[neighbors2[dir_dia[(dir+1) % 4]]] = (dir+3)%4
                    update_strength(neighbors2[dir_dia[(dir+1) % 4]],(dir+3)%4)
            return
        elif any(ne.owner==0 for ne in neighbors):
            target, direction = max(
                ((neighbor, direction) for direction, neighbor in enumerate(game_map.neighbors(square)) if
                 neighbor.owner != myID), default=(None, STILL), key=lambda t: heuristic(t[0],t[1]))
            score = -1
            st=1000
            if target is not None:
                score = heuristic(target,direction)
                if target.strength >= square.strength or target_strength(square, direction) >= 280:
                    direction = STILL
                for i in (NORTH, EAST, SOUTH, WEST):
                    t1 = neighbors[dir1[i]]
                    if t1.owner == myID:
                        t2, direction2 = max(((neighbors[dir3[i][k]], k) for k in range(4) if neighbors[dir3[i][k]].owner != myID and k!=rev[i]),
                                    default=(None, None), key=lambda t: heuristic(t[0],t[1]))
                        if t2 is not None and (t1.strength + t1.production) <= t2.strength :
                            eva = heuristic(t2,direction2)
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
             dic[square]= find_nearest_enemy_direction(square)
             update_strength(square, direction)
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
            get_move(square)
    for key in dic:
        c = c + 1
        p+=key.production
        st_s += key.strength
        if key.strength < key.production*3:
            moves.append(Move(key,STILL))
        else:
            moves.append(Move(key, dic[key]))
    tn+=1
    dic_strength={}
    hlt.send_frame(moves)

