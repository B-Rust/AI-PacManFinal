# CS 4365 Course Final Project
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

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='OffensiveReflexAgent', second='DefensiveReflexAgent'):

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
    ghostDistances = []
    capsuleDistance = []
    invaderDistance = []
    features = util.Counter()
    current = self.getCurrentObservation()
    successor = self.getSuccessor(gameState, action)

    presentState = current.getAgentState(self.index)
    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    foodList = self.getFood(successor).asList()
    capsuleList = self.getCapsules(successor)

    # Score of capturing the food
    features['successorScore'] = myState.numCarrying + self.getScore(successor)

    for capsule in capsuleList:
        capsuleDistance.append(self.getMazeDistance(myPos, capsule))

    if len(capsuleDistance) > 0:
        smallestDistance = min(capsuleDistance)
        features['distanceToCapsule'] = smallestDistance

    if current is not None and myPos in self.getCapsules(current):
        features['distanceToCapsule'] = -100000

    enemies = [current.getAgentState(i) for i in self.getOpponents(current)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() is not None]
    ghosts = [b for b in enemies if not b.isPacman and b.getPosition() is not None and not b.scaredTimer > 0]

    # Runaway
    for ghost in ghosts:
        ghostDistances.append(self.getMazeDistance(myPos, ghost.getPosition()))

    if myState.isPacman and len(ghostDistances) > 0:
        smallestDistance = min(ghostDistances)

        if smallestDistance < 5:
            features['avoidDeadEnd'] = 1 if len(successor.getLegalActions(self.index)) < 3 else 0

        if smallestDistance < 4:
            features['getHome'] = self.getMazeDistance(myPos, self.start)

        if smallestDistance < 3:
            features['enemyNear'] = smallestDistance

    # Go after Pac-Man
    for pacman in invaders:
        invaderDistance.append(self.getMazeDistance(myPos, pacman.getPosition()))

    if len(invaderDistance) > 0:
        smallestDistance = min(invaderDistance)

        if myState.scaredTimer <= 0:
            features['crossingPrey'] = smallestDistance
        else:

            if smallestDistance < 3:
                features['crossingPrey'] = -smallestDistance

            features['avoidDeadEnd'] = 1 if len(successor.getLegalActions(self.index)) < 3 else 0

    if presentState.numCarrying > 2:
        features['getHome'] = self.getMazeDistance(myPos, self.start) * (
                myState.numCarrying / (float(len(foodList) + 1)))

    if len(foodList) > 0:  # This should always be True, but better safe than sorry
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance

    if action == Directions.STOP:
        features['stop'] = 1

    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]

    if action == rev:
        features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate. They can be either
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
      features = DummyAgent.getFeatures(self, gameState, action)
      lastPlace = self.getPastPlace(8)
      successor = self.getSuccessor(gameState, action)
      myState = successor.getAgentState(self.index)
      myPos = myState.getPosition()
      if myPos in lastPlace:
          features['previous'] = 1
      return features

  def getPastPlace(self, t):
      return [lastState.getAgentState(self.index).getPosition() for lastState in self.observationHistory[-t:]]

  def getWeights(self, gameState, action):
      return {
          'successorScore': 150,  # Try to score more
          'distanceToFood': -1,
          'distanceToCapsule': -1,
          'getHome': -10,
          'avoidDeadEnd': -100,
          'enemyNear': 100,
          'crossingPrey': -0.75,  # Don't worry too much about defending
          'stop': -100,
          'reverse': -2,
          'previous': -50  # Avoid stalemates
      }

class DefensiveReflexAgent(DummyAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like. It is not the best or only way to make
  such an agent.
  """

  def getWeights(self, gameState, action):
      return {
          'successorScore': 100,
          'distanceToFood': -1,
          'distanceToCapsule': -1,
          'getHome': -10,
          'avoidDeadEnd': -100,
          'enemyNear': 100,
          'crossingPrey': -100,  # Care more about defending
          'stop': -100,
          'reverse': -2
      }