import random

pieceScore = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0
DEPTH = 2
def findRandomMove(validMoves):
    return random.choice(validMoves)
#
# def findBestMoveMinMax(gs, validMoves):
#     global nextMove
#     nextMove = None
#     random.shuffle(validMoves)
#     findMoveMinMax(gs, validMoves, DEPTH, gs.whiteToMove)
#     return nextMove
#
# def findMoveMinMax(gs, validMoves, depth, whiteToMove):
#     global nextMove
#     if depth == 0:
#         return scoreBoard(gs)
#     if whiteToMove:
#         maxScore = -CHECKMATE
#         for move in validMoves:
#             gs.makeMove(move)
#             nextMoves = gs.getValidMoves()
#             score = findMoveMinMax(gs, nextMoves, depth - 1, False)
#             if score > maxScore:
#                 maxScore = score
#                 if depth == DEPTH:
#                     nextMove = move
#             gs.undoMove()
#         return maxScore
#     else:
#         minScore = CHECKMATE
#         for move in validMoves:
#             gs.makeMove(move)
#             nextMoves = gs.getValidMoves()
#             score = findMoveMinMax(gs, nextMoves, depth - 1, True)
#             if score < minScore:
#                 minScore = score
#                 if depth == DEPTH:
#                     nextMove = move
#             gs.undoMove()
#         return minScore
#
# def findBestMoveNegaMax(gs, validMoves):
#     global nextMove
#     nextMove = None
#     random.shuffle(validMoves)
#     negaMax(gs, validMoves, DEPTH, 1 if gs.whiteToMove else -1)
#     return nextMove
#
# def negaMax(gs, validMoves, depth, turnMultiplier):
#     global nextMove
#     if depth == 0:
#         return turnMultiplier * scoreBoard(gs)
#     maxScore = -CHECKMATE
#     for move in validMoves:
#         gs.makeMove(move)
#         nextMoves = gs.getValidMoves()
#         score = -negaMax(gs, nextMoves, depth - 1, -turnMultiplier)
#         if score > maxScore:
#             maxScore = score
#             if depth == DEPTH:
#                 nextMove = move
#         gs.undoMove()
#     return maxScore

def findBestMoveAlphaBeta(gs, validMoves , depth):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    global DEPTH
    DEPTH = depth
    # print(DEPTH)
    alphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
    return nextMove

def alphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)
    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -alphaBeta(gs, nextMoves, depth - 1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
        alpha = max(alpha, maxScore)
        if alpha >= beta:
            break
    return maxScore

def scoreBoard(gs):
    if gs.checkmate:
        if gs.whiteToMove:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gs.stalemate:
        return STALEMATE
    score = scoreMaterial(gs.board)
    return score

# Score the board based on material
def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score