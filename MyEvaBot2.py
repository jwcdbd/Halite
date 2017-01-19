import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random
import math
import time
import sys
import cProfile

myID, game_map = hlt.get_init()
hlt.send_init("MyPythonBot")
dir2=[[0,1,3],[3,7,10],[8,10,11],[1,8,4]]
dir1=[2,6,9,5] #N E S W
dir_dia=[1,3,10,8]#NW NE SE SW
Pat=[0, 0, 0, 0]
strength_max=[0, 0, 0, 0]
strength_min=[0, 0, 0, 0]
dic={}
def find_nearest_enemy_direction(square):
    path_strength=0
    direction = NORTH
    max_distance = min(game_map.width, game_map.height) / 2
    for d in (NORTH, EAST, SOUTH, WEST):
        path = 0
        distance = 0
        current = square
        while current.owner == myID and distance < max_distance:
            path = path + current.strength / math.exp(distance / min(game_map.width, game_map.height))
            distance += 1
            current = game_map.get_target(current, d)
        if distance < max_distance:
            direction = d
            path_strength = path
            max_distance = distance
    return direction,path_strength

def get_move(square):
    direction = STILL
    eva=float("-inf")
    score = float("-inf")
    neighbors = [neighbor for neighbor in game_map.neighbors(square,2)]
    enemy_e = any(ne.owner != myID for ne in neighbors)  # find out if there is enemy in distance<=2
    if enemy_e > 0:
        for i in (NORTH, EAST, SOUTH, WEST):
            target = neighbors[dir1[i]]
            enemy_group = [neighbors[k] for k in dir2[i] if neighbors[k].owner not in (0, myID)]
            self_group= [neighbors[k] for k in dir2[i] if neighbors[k].owner == myID]
            n_enemy = len(enemy_group)
            n_self = len(self_group)
            strength_min[i],b = min(((neighbors[k].strength,neighbors[k].production) for k in dir2[i] if neighbors[k].owner!=myID), default=(0,0),key=lambda t: t[0])
            p_2 = sum(neighbors[k].production for k in dir2[i] if neighbors[k].owner != myID) #potential production gain
            strength_enemy_total = sum(en.strength for en in enemy_group) #possible total damage, reinforcement enemy strength happend in the cell
            strength_my_total = sum(s.strength for s in self_group) # possible total loss, reinforcement strength in the cell
            strength_max[i] = max((en.strength for en in enemy_group), default=(0)) # possible move of the cell of the
            # enemy

            Pat[i] = 1/(1+math.exp(-min(((strength_max[i]+strength_enemy_total*0.02)-(
                target.strength+0.02*strength_my_total)+1),40))*(target.owner!=myID))
            D=min((target.strength+strength_max[i]+strength_enemy_total*0.02),Pat[i]*square.strength) # extra damage to
            #  the target if move to the target if target ==myID, and strength is large, then the Pat is small, meaning the damage is small
            Dtotal=sum( min(D,e.strength) for e in enemy_group)
            Ltotal=sum( min(D,e.strength) for e in self_group)*math.exp(-(strength_max[i]+1)/(target.strength+1)*3)*(
                target.owner!=0)
            Pwin_1 = (square.strength >= target.strength) * (target.owner != myID)
            #Pwin_1=1/(1+math.exp(-min((square.strength-target.strength-3),40)/1))*(target.owner!=myID)
            Pwin_2=(target.owner == myID)*(((target.strength+square.strength) >= strength_min[i])*(target.strength < strength_min[i]))
            #Pwin_2=0.001
            ProdTotal = 5*Pwin_1*(0.1*p_2+target.production)+5*p_2*0.1*Pwin_2
            eva=ProdTotal+Dtotal-Ltotal
            if eva > score:
                score = eva
                direction=i
        strength=float(square.strength)+square.production
        #enemy_group = [neighbors[i] for i in dir1 if neighbors[i].owner not in (0,myID)]
        D=min(max((1/(1+math.exp(-min((neighbors[k].strength-strength+1),40))))*neighbors[k].strength*(neighbors[k].owner not in (0,myID)) for k in dir1), strength)
        p_2=sum((neighbors[k].production for k in dir1 if neighbors[k].owner!=myID))
        ProdTotal_s = 5 * 0.1 *p_2
        Dtotal_s = sum(min(D,neighbors[k].strength*(neighbors[k].owner not in (0,myID))) for k in dir1)
        Lsecond = min(sum((1-math.exp(-strength_max[k]/(neighbors[dir1[k]].strength+1)*3))*neighbors[dir1[k]].strength for k in range(4)),strength-D)
        Ltotal_s = sum(min(D,neighbors[k].strength*(neighbors[k].owner == myID)) for k in dir1)+Lsecond
        eva = ProdTotal_s +Dtotal_s - Ltotal_s
        if eva >= score :
            direction=STILL
        target=game_map.get_target(square,direction)
        if target.owner==myID :
            dic[target]=1
        return Move(square,direction)
    else:
        d, path_strength= find_nearest_enemy_direction(square)

        if path_strength * (1 - math.exp(-square.strength/(square.production*3+0.1))) > 10:
            return Move(square, d)
        else:
            return Move(square, STILL)

while True:
    game_map.get_frame()

    moves = [get_move(square) for square in game_map if square.owner == myID]
    hlt.send_frame(moves)
