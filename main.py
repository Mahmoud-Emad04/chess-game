import pygame as p
import computer
from engine import GameState
from moves import MoveGenerator, Move

WIDTH = HEIGHT = 512
SIDEBAR_WIDTH = 200
DIMENSION = 8  # Chess board is 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15  # For animations later on
IMAGES = {}
class ChessGame:
    def __init__(self):
        self.screen = None
        self.clock = None
        self.gs = GameState()
        self.validMoves = self.gs.getValidMoves()
        self.moveMade = False
        self.sqSelected = None  # tuple: (row, col)
        self.playerClicks = []  # Keep track of player clicks (two tuples: [(6, 4), (4, 4)])
        self.selectedPieceMoves = []  # Store valid moves for the selected piece
        self.capturedPieces = {"w": [], "b": []}  # Store captured pieces
        self.playerOne, self.playerTwo = None, None
        self.animate = False

    def loadImages(self):
        pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
        for piece in pieces:
            IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

    def initializeGame(self):
        p.init()
        p.display.set_caption("Chess Game")
        self.screen = p.display.set_mode((WIDTH + SIDEBAR_WIDTH, HEIGHT))
        self.clock = p.time.Clock()
        self.screen.fill(p.Color("white"))
        self.loadImages()
        self.playerOne, self.playerTwo = self.showStartWindow()

    def mainLoop(self):
        running = True
        while running:
            humanTurn = (self.gs.whiteToMove and self.playerOne) or (not self.gs.whiteToMove and self.playerTwo)
            for e in p.event.get():
                if e.type == p.QUIT:
                    running = False
                elif e.type == p.MOUSEBUTTONDOWN:
                    if humanTurn:
                        self.handleMouseClick(e)
                elif e.type == p.KEYDOWN:
                    self.handleKeyPress(e)
            if not humanTurn:
                self.handleAIMove()
            if self.moveMade:
                if self.animate:
                    self.animateMove(self.gs.moveLog[-1])
                self.validMoves = self.gs.getValidMoves()
                self.moveMade = False
            self.drawGameState()
            if self.gs.checkmate or self.gs.stalemate:
                self.showEndGameMessage("Checkmate" if self.gs.checkmate else "Stalemate", "Black" if self.gs.whiteToMove else "White")
                running = False
            self.clock.tick(MAX_FPS)
            p.display.flip()



    def handleMouseClick(self, event):
        location = p.mouse.get_pos()  # location of the mouse (x, y)
        if location[0] < WIDTH:  # Click on the board
            col, row = (location[0] // SQ_SIZE), (location[1] // SQ_SIZE)
            if self.sqSelected == (row, col):  # The user clicked the same square twice
                self.sqSelected = None  # Deselect
                self.playerClicks = []  # Clear player clicks
                self.selectedPieceMoves = []  # Clear valid moves for the selected piece
            else:
                self.sqSelected = (row, col)
                self.playerClicks.append(self.sqSelected)  # Append for both 1st and 2nd clicks
                self.selectedPieceMoves = [move for move in self.validMoves if move.startRow == row and move.startCol == col]
            if len(self.playerClicks) == 2:  # After the 2nd click
                move = Move(self.playerClicks[0], self.playerClicks[1], self.gs.board)
                print(move.getChessNotation())
                for i in range(len(self.validMoves)):
                    if move == self.validMoves[i]:
                        if move.isPawnPromotion:
                            choice = self.showPromotionChoices(self.gs.whiteToMove)
                            self.gs.makeMove(self.validMoves[i], choice)
                        else:
                            self.gs.makeMove(self.validMoves[i])
                        self.moveMade = True
                        self.animate = True
                        self.sqSelected = None  # Reset user clicks
                        self.playerClicks = []
                        self.selectedPieceMoves = []  # Clear valid moves for the selected piece
                        if move.pieceCaptured != "--":
                            self.capturedPieces[move.pieceCaptured[0]].append(move.pieceCaptured)
                            p.mixer.Sound('sounds/capture.mp3').play()
                        else:
                            p.mixer.Sound('sounds/move-self.mp3').play()
                if not self.moveMade:
                    self.playerClicks = [self.sqSelected]

    def handleKeyPress(self, event):
        if event.key == p.K_z:
            self.gs.undoMove()
            self.moveMade = True
            self.animate = False
        if event.key == p.K_r:
            self.resetGame()

    def handleAIMove(self):
        AIMove = computer.findBestMoveAlphaBeta(self.gs, self.validMoves)
        if AIMove is None:
            AIMove = computer.findRandomMove(self.validMoves)
        self.gs.makeMove(AIMove)
        self.moveMade = True
        if AIMove.pieceCaptured != "--":
            self.capturedPieces[AIMove.pieceCaptured[0]].append(AIMove.pieceCaptured)
            p.mixer.Sound('sounds/capture.mp3').play()
        else:
            p.mixer.Sound('sounds/move-self.mp3').play()

    def resetGame(self):
        self.gs = GameState()
        self.validMoves = self.gs.getValidMoves()
        self.sqSelected = None
        self.playerClicks = []
        self.selectedPieceMoves = []
        self.capturedPieces = {"w": [], "b": []}
        self.moveMade = False
    # highlight moves
    def highlightSquares(self):
        if self.sqSelected != None:
            r, c = self.sqSelected
            if self.gs.board[r][c][0] == ('w' if self.gs.whiteToMove else 'b'):
                s = p.Surface((SQ_SIZE, SQ_SIZE))
                s.set_alpha(150)
                s.fill(p.Color('blue'))
                self.screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
                s.fill(p.Color('yellow'))
                for move in self.validMoves:
                    if move.startRow == r and move.startCol == c:
                    #     if (move.endRow+move.endCol)%2 == 0:
                    #         s.fill(p.Color('blue'))
                    #     else:
                    #         s.fill(p.Color('lightblue'))
                        self.screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

    def drawGameState(self):
        self.drawBoard()
        self.highlightSquares()
        self.drawPieces()
        self.drawSidebar()

    def drawBoard(self):
        colors = [p.Color((235,236,208)), p.Color((115,149,82))]
        checkColor = p.Color("red")  # Color for the king in check
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                color = colors[((r + c) % 2)]
                p.draw.rect(self.screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
                # Check Color
                if self.gs.inCheck and ((self.gs.whiteToMove and (r, c) == self.gs.whiteKingLocation) or
                                        (not self.gs.whiteToMove and (r, c) == self.gs.blackKingLocation)):
                    color = checkColor
                # Check Sound
                if self.gs.inCheck and not hasattr(self.gs, 'checkSoundPlayed'):
                    p.mixer.Sound('sounds/move-check.mp3').play()
                    self.gs.checkSoundPlayed = True
                elif not self.gs.inCheck:
                    if hasattr(self.gs, 'checkSoundPlayed'):
                        del self.gs.checkSoundPlayed
                # Checkmate Sound
                if self.gs.checkmate and not hasattr(self.gs, 'checkmateSoundPlayed'):
                    p.mixer.Sound('sounds/chess_com_checkmate.mp3').play()
                    self.gs.checkmateSoundPlayed = True
                elif not self.gs.checkmate:
                    if hasattr(self.gs, 'checkmateSoundPlayed'):
                        del self.gs.checkmateSoundPlayed
                p.draw.rect(self.screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    def drawPieces(self):
        for r in range(DIMENSION):
            for c in range(DIMENSION):
                piece = self.gs.board[r][c]
                if piece != "--":
                    self.screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

    def drawSidebar(self):
        # Draw the sidebar background
        sidebarRect = p.Rect(WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
        p.draw.rect(self.screen, p.Color("gray"), sidebarRect)

        # Set up font
        font = p.font.SysFont("Helvetica", 24, True, False)

        # Display whose turn it is using color
        turnColor = p.Color("white") if self.gs.whiteToMove else p.Color("black")
        turnRect = p.Rect(WIDTH + 10, 10, 30, 30)
        p.draw.rect(self.screen, turnColor, turnRect)
        # Display captured pieces
        yOffset = 60
        pieceSize = SQ_SIZE // 2  # Smaller size for captured pieces
        for color, pieces in self.capturedPieces.items():
            colorText = "White captured:" if color == "w" else "Black captured:"
            colorObject = font.render(colorText, 0, p.Color("Black"))
            self.screen.blit(colorObject, (WIDTH + 10, yOffset))
            yOffset += 30
            xOffset = WIDTH + 10
            for i, piece in enumerate(pieces):
                pieceImage = p.transform.scale(IMAGES[piece], (pieceSize, pieceSize))
                self.screen.blit(pieceImage, (xOffset, yOffset))
                xOffset += pieceSize + 5  # Move to the right for the next piece
                if (i + 1) % 4 == 0:  # Move to the next row after 4 pieces
                    xOffset = WIDTH + 10
                    yOffset += pieceSize + 5  # Add some space between rows
            yOffset += pieceSize + 10  # Add some space between different color sections

    def showEndGameMessage(self, message, winner):
        font = p.font.SysFont("Helvetica", 32, True, False)
        if winner:
            if message == "Checkmate":
                message = f"{winner} wins by checkmate!"
            else:
                message = "It's a stalemate!"

        textObject = font.render(message, 0, p.Color("Black"))
        textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH // 2 - textObject.get_width() // 2, HEIGHT // 2 - textObject.get_height() // 2)
        self.screen.blit(textObject, textLocation)

        # Draw buttons
        playAgainButton = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 50)
        quitButton = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 120, 200, 50)
        p.draw.rect(self.screen, p.Color("green"), playAgainButton)
        p.draw.rect(self.screen, p.Color("red"), quitButton)

        playAgainText = font.render("Play Again", 0, p.Color("Black"))
        quitText = font.render("Quit", 0, p.Color("Black"))
        self.screen.blit(playAgainText, playAgainButton.move(50, 10))
        self.screen.blit(quitText, quitButton.move(75, 10))

        p.display.flip()

        waiting = True
        while waiting:
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    location = p.mouse.get_pos()
                    if playAgainButton.collidepoint(location):
                        self.resetGame()
                        self.mainLoop()
                        waiting = False
                    elif quitButton.collidepoint(location):
                        p.quit()
                        exit()

    def showStartWindow(self):
        font = p.font.SysFont("Helvetica", 32, True, False)
        self.screen.fill(p.Color("lightblue"))

        titleText = font.render("Choose Game Mode", 0, p.Color("Black"))
        titleLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4 - titleText.get_height() // 2)
        self.screen.blit(titleText, titleLocation)

        vsPlayerButton = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
        vsComputerButton = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
        p.draw.rect(self.screen, p.Color("blue"), vsPlayerButton, border_radius=10)
        p.draw.rect(self.screen, p.Color("blue"), vsComputerButton, border_radius=10)

        vsPlayerText = font.render("Player vs Player", 0, p.Color("white"))
        vsComputerText = font.render("Player vs Computer", 0, p.Color("white"))
        self.screen.blit(vsPlayerText, vsPlayerButton.move(20, 10))
        self.screen.blit(vsComputerText, vsComputerButton.move(10, 10))

        p.display.flip()

        waiting = True
        while waiting:
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    location = p.mouse.get_pos()
                    if vsPlayerButton.collidepoint(location):
                        return True, True
                    elif vsComputerButton.collidepoint(location):
                        return self.showColorChoiceWindow()

    def showColorChoiceWindow(self):
        font = p.font.SysFont("Helvetica", 32, True, False)
        self.screen.fill(p.Color("lightgreen"))

        titleText = font.render("Choose Your Color", 0, p.Color("Black"))
        titleLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH // 2 - titleText.get_width() // 2, HEIGHT // 4 - titleText.get_height() // 2)
        self.screen.blit(titleText, titleLocation)

        whiteButton = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)
        blackButton = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)
        p.draw.rect(self.screen, p.Color("white"), whiteButton, border_radius=10)
        p.draw.rect(self.screen, p.Color("black"), blackButton, border_radius=10)

        whiteText = font.render("White", 0, p.Color("Black"))
        blackText = font.render("Black", 0, p.Color("White"))
        self.screen.blit(whiteText, whiteButton.move(60, 10))
        self.screen.blit(blackText, blackButton.move(60, 10))

        p.display.flip()

        waiting = True
        while waiting:
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    location = p.mouse.get_pos()
                    if whiteButton.collidepoint(location):
                        return True, False
                    elif blackButton.collidepoint(location):
                        return False, True

    def showPromotionChoices(self, isWhite):
        font = p.font.SysFont("Helvetica", 24, True, False)
        promotionRect = p.Rect(WIDTH + 10, HEIGHT // 2 - 100, 180, 200)
        p.draw.rect(self.screen, p.Color("lightyellow"), promotionRect)

        titleText = font.render("Promote to:", 0, p.Color("Black"))
        self.screen.blit(titleText, promotionRect.move(10, 10))

        pieces = ["Q", "R", "N", "B"]
        pieceImages = ["wQ", "wR", "wN", "wB"] if isWhite else ["bQ", "bR", "bN", "bB"]
        buttons = []
        for i, piece in enumerate(pieces):
            button = p.Rect(WIDTH + 20, HEIGHT // 2 - 50 + i * 40, 160, 30)
            p.draw.rect(self.screen, p.Color("blue"), button, border_radius=5)
            pieceImage = p.transform.scale(IMAGES[pieceImages[i]], (30, 30))
            self.screen.blit(pieceImage, button.move(10, 0))
            pieceText = font.render(piece, 0, p.Color("white"))
            self.screen.blit(pieceText, button.move(50, 0))
            buttons.append((button, piece))

        p.display.flip()

        waiting = True
        while waiting:
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    location = p.mouse.get_pos()
                    for button, piece in buttons:
                        if button.collidepoint(location):
                            return piece
# animation for move
    def animateMove(self, move):
        dR = move.endRow - move.startRow
        dC = move.endCol - move.startCol
        framesPerSquare = 10
        frameCount = (abs(dR) + abs(dC)) * framesPerSquare
        for frame in range(frameCount + 1):
            r, c = (move.startRow + dR * frame / frameCount, move.startCol + dC * frame / frameCount)
            self.drawBoard()
            self.drawPieces()
            # erase the piece from ending square
            color = (move.endRow + move.endCol) % 2
            endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            p.draw.rect(self.screen, p.Color("white"), endSquare)
            # draw captured piece back
            if move.pieceCaptured != "--":
                self.screen.blit(IMAGES[move.pieceCaptured], endSquare)
            # draw moving piece
            self.screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
            p.display.flip()
            self.clock.tick(150)


if __name__ == "__main__":
    game = ChessGame()
    game.initializeGame()
    game.mainLoop()