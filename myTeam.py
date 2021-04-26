# CS 4365 Course Project Friendly Competition
# Juan Perez - jjp170130
# Ben Rust - bjr170630
# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

from captureAgents import CaptureAgent
import random, util
from game import Directions
from util import nearestPoint
from distanceCalculator import Distancer

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """
    self.start = gameState.getAgentPosition(self.index)

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start, pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid placement (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid placement was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveReflexAgent(DummyAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    distancer = Distancer(gameState.data.layout)
    distancer.getMazeDistances()
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodList = self.getFood(successor).asList()
    features['foodLeft'] = len(foodList)#self.getScore(successor)

    #Run away from ghosts when on other side
    indexOfEnemy = self.getOpponents(successor)
    positionOfEnemy = [successor.getAgentPosition(index) for index in indexOfEnemy if not successor.getAgentState(index).isPacman] #only adds ghosts to the tally
    distanceOfEnemy = []
    for pos in positionOfEnemy:
        distanceOfEnemy.append(distancer.getDistance(successor.getAgentPosition(self.index), pos))
    enemyNear = 10
    if len(distanceOfEnemy) > 0 and min(distanceOfEnemy) < 3 and successor.getAgentState(self.index).isPacman: #only cares about ghosts if its a pacman and the distance is less than three
        enemyNear = min(distanceOfEnemy)
    features['enemyNear'] = enemyNear


    amountCarrying = gameState.getAgentState(self.index).numCarrying
    prey = gameState.data.layout.width // 2
    if gameState.isOnRedTeam(self.index):
        prey = prey - 1

    positionOfTarget = [(prey, y) for y in range(0, gameState.data.layout.height)]

    distancer = Distancer(gameState.data.layout)
    distancer.getMazeDistances()

    targetDistances = []
    for placement in positionOfTarget:
        try:
            targetDistances.append(distancer.getDistance(placement, successor.getAgentPosition(self.index)))
        except:
            0

    smallestDist = min(targetDistances)
    features['getHome'] = 30
    if amountCarrying > 0:
        features['getHome'] = smallestDist

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)

    prey = gameState.data.layout.width // 2
    if not gameState.isOnRedTeam(self.index):
        prey = prey - 1

    positionOfTarget = [(prey, y) for y in range(0, gameState.data.layout.height)]

    distancer = Distancer(gameState.data.layout)
    distancer.getMazeDistances()

    targetsReach = []
    for placement in positionOfTarget:
        try:
            smallestDistance = min([distancer.getDistance(placement, enemy.getPosition()) for enemy in enemies])
            if smallestDistance > 10:
                targetsReach.append(placement)
        except:
            0

    myPos = successor.getAgentState(self.index).getPosition()
    nearestGhost = min([distancer.getDistance(myPos, enemy.getPosition()) for enemy in enemies])
    distanceToPacman = [distancer.getDistance(myPos, placement) for placement in targetsReach]

    if(gameState.getAgentState(self.index).isPacman):
        features['crossingPrey'] = 0
        features['enemyNear'] = 0 if nearestGhost > 4 else nearestGhost
    else:
        features['enemyNear'] = 0
        features['crossingPrey'] = min(distanceToPacman) if len(distanceToPacman) > 0 else 0

    # Compute distance to the nearest food

    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      smallestDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = smallestDistance
    return features

  def getWeights(self, gameState, action):
    return {'foodLeft': -100, 'distanceToFood': -1, 'enemyNear': 100, 'getHome': -100, 'crossingPrey': -100, "numInvaders": -20}

class DefensiveReflexAgent(DummyAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    distancer = Distancer(gameState.data.layout)
    distancer.getMazeDistances()
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)

    if len(invaders) == 0:
        middle = (gameState.data.layout.width/2, gameState.data.layout.height/2)
        distanceToMiddle = self.getMazeDistance(myPos, middle)
        features['waitmiddle'] = distanceToMiddle

    if len(invaders) > 0:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
        features['invaderDistance'] = min(dists)

    if action == Directions.STOP:
      features['stop'] = 1

    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]

    if action == rev:
      features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2, 'waitmiddle': -100}