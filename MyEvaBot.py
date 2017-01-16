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
def find_nearest_enemy_direction(square):
    path_strength=0
    direction = NORTH
    max_distance = min(game_map.width, game_map.height) / 2
    for d in (NORTH, EAST, SOUTH, WEST):
        path = 0
        distance = 0
        current = square
        while current.owner == myID and distance < max_distance:
            path = path+current.strength
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
    enemy_dir = [dir for dir in range(4) if neighbors[dir1[dir]].owner != myID] # find out the enemy direction
    if len(enemy_dir)>0:
        for i in (NORTH, EAST, SOUTH, WEST):
            target = neighbors[dir1[i]]
            n_enemy = sum(neighbors[k].owner != myID for k in dir2[i])+(i in enemy_dir) # the overkill is in the diagonal direction
            n_self = 5-n_enemy # total number of self (3-n_enemy+1) 1 is from the square move
            p_2 = sum(neighbors[k].production for k in dir2[i] if neighbors[k].owner != myID) #possible move for the next round
            p_d = target.production
            strength_enemy_total = sum(neighbors[k].strength for k in dir2[i] if neighbors[k].owner not in (0, myID)) #possible total damage, reinforcement enemy strength happend in the cell
            strength_my_total = sum(neighbors[k].strength for k in dir2[i] if neighbors[k].owner == myID) +square.strength # possible total loss, reinforcement strength in the cell
            strength_neig = [neighbors[k].strength for k in dir2[i] if neighbors[k].owner != myID]
            strength_neig.append(0)
            strength_max = max(strength_neig) # possible move of the cell of the enemy
            strength_min = min(strength_neig) #possible move of the cell of the enemy
            if target.owner != myID:
                if target.strength >= square.strength:
                    continue
                td = sum(min([neighbors[k].strength, target.strength]) for k in dir2[i] if neighbors[k].owner not in (0, myID))
                sd = sum(min([neighbors[k].strength, target.strength]) for k in dir2[i] if neighbors[k].owner == myID)+min(target.strength,square.strength)
                eva=(0.1*p_2+(0.5+(target.owner==0)*0.5)*p_d-square.production)*4+0.2*td-0.1*sd+0.1*(square.strength-strength_min)+0.01*(square.strength-strength_max)+0.05*(strength_my_total-strength_enemy_total)
            else:
                td = sum(min([neighbors[k].strength, square.strength]) for k in dir2[i] if neighbors[k].owner not in (0, myID))
                sd = sum(min([neighbors[k].strength, square.strength]) for k in dir2[i] if neighbors[k].owner == myID) + square.strength
                eva=(0.1*p_2+0.5*p_d-square.production)*4+0.2*td-0.1*sd-8*math.exp((square.strength+target.strength-255)/500)+0.01*(strength_max-target.strength)+0.05*(strength_my_total-strength_enemy_total)
            if eva >score:
                score= eva
                direction=i
        strength_enemy_total = sum(neighbors[k].strength for k in dir1 if neighbors[k].owner not in (0, myID))  # possible total damage, reinforcement enemy strength happend in the cell
        strength_my_total = sum(neighbors[k].strength for k in dir1 if neighbors[k].owner == myID) + square.strength  # possible total loss, rein
        td = sum(min([neighbors[k].strength, square.strength]) for k in dir1 if neighbors[k].owner != myID and neighbors[k].owner != 0)
        sd = sum(min([neighbors[k].strength, square.strength]) for k in dir1 if neighbors[k].owner == myID) + square.strength
        eva= square.production*4+0.2*td-0.1*sd-8*math.exp((square.strength-255)/500)+0.05*(strength_my_total-strength_enemy_total)+4*math.exp(-square.strength / (square.production * 2 + 0.01))
        if eva>score:
            direction=STILL
        return Move(square,direction)
    else:
        d, path_strength= find_nearest_enemy_direction(square)

        if path_strength * (1 - math.exp(-square.strength / (square.production * 2 + 0.01))) > 80:
            return Move(square, d)
        else:
            return Move(square, STILL)

while True:
    game_map.get_frame()

    moves = [get_move(square) for square in game_map if square.owner == myID]
    hlt.send_frame(moves)
