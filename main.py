import time
import pygame as p
import computer
from engine import GameState
from moves import MoveGenerator, Move

WIDTH = HEIGHT = 512
SIDEBAR_WIDTH = 300
DIMENSION = 8  # Chess board is 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15  # For animations later on
IMAGES = {}
depth = 2
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

        self.timeLeft = {"w": 900, "b": 900}  # 15 minutes (900 seconds) for each player
        self.lastUpdateTime = time.time()  # To track elapsed time
        self.timerRunning = True  # Timer state
        self.increment = 2  # Increment in seconds per move (optional)

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

    def updateTimers(self):
        # Calculate elapsed time
        currentTime = time.time()
        if self.timerRunning:
            elapsedTime = currentTime - self.lastUpdateTime
            self.lastUpdateTime = currentTime
            # Deduct time from the active player
            currentPlayer = "w" if self.gs.whiteToMove else "b"
            self.timeLeft[currentPlayer] -= elapsedTime
            if self.timeLeft[currentPlayer] <= 0:
                self.showEndGameMessage("Timeout", "Black" if currentPlayer == "w" else "White")
                self.timerRunning = False



    def drawTimers(self):
        # Fonts for the timers
        font = p.font.SysFont("Helvetica", 28, True, False)
        timerFont = p.font.SysFont("Helvetica", 24, True, False)

        # White Timer
        whiteTimerText = font.render("White Time:", 0, p.Color("white"))
        self.screen.blit(whiteTimerText, (WIDTH + 10, 235))
        whiteTime = self.formatTime(self.timeLeft["w"])
        whiteTimerValue = timerFont.render(whiteTime, 0, p.Color("white"))
        self.screen.blit(whiteTimerValue, (WIDTH + 10, 265))

        # Black Timer
        blackTimerText = font.render("Black Time:", 0, p.Color("black"))
        self.screen.blit(blackTimerText, (WIDTH + 10, 450))
        blackTime = self.formatTime(self.timeLeft["b"])
        blackTimerValue = timerFont.render(blackTime, 0, p.Color("black"))
        self.screen.blit(blackTimerValue, (WIDTH + 10, 480))

    @staticmethod
    def formatTime(seconds):
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02}:{seconds:02}"
    def mainLoop(self):
        running = True
        self.lastUpdateTime = time.time()  # Initialize the timer
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

            # Update timers only during active gameplay
            if self.timerRunning:
                self.updateTimers()

            if self.moveMade:
                if self.animate:
                    self.animateMove(self.gs.moveLog[-1])
                self.validMoves = self.gs.getValidMoves()
                self.moveMade = False

            self.drawGameState()

            if self.gs.checkmate or self.gs.stalemate:
                self.showEndGameMessage("Checkmate" if self.gs.checkmate else "Stalemate",
                                        "Black" if self.gs.whiteToMove else "White")
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
        AIMove = computer.findBestMoveAlphaBeta(self.gs, self.validMoves , depth)
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
        self.drawTimers()

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
        p.draw.rect(self.screen, p.Color("lightgray"), sidebarRect)

        sidebarRect = p.Rect(WIDTH, 72, SIDEBAR_WIDTH, 220)
        p.draw.rect(self.screen, p.Color("Black"), sidebarRect)

        sidebarRect = p.Rect(WIDTH, 72+220, SIDEBAR_WIDTH, 220)
        p.draw.rect(self.screen, p.Color("white"), sidebarRect)

        # Set up fonts
        titleFont = p.font.SysFont("Helvetica", 28, True, False)
        infoFont = p.font.SysFont("Helvetica", 20, True, False)

        # Draw the turn indicator
        turnColor = "white" if self.gs.whiteToMove else "black"
        turnIndicatorRect = p.Rect(WIDTH + 20, 20, SIDEBAR_WIDTH - 40, 40)
        p.draw.rect(self.screen, p.Color(turnColor), turnIndicatorRect, border_radius=10)
        turnText = titleFont.render(f"{turnColor.capitalize()} to move", 0,
                                    p.Color("black" if turnColor == "white" else "white"))
        self.screen.blit(turnText, turnIndicatorRect.move(20, 5))

        # Draw White Player Info (Top Half)
        whiteTitle = titleFont.render("White Captured Pieces", 0, p.Color("white"))
        self.screen.blit(whiteTitle, (WIDTH + 10, 80))

        # whiteCapturedTitle = infoFont.render("Captured Pieces", 0, p.Color("white"))
        # self.screen.blit(whiteCapturedTitle, (WIDTH + 10, 110))

        yOffset = 120  # Start below the title
        pieceSize = SQ_SIZE // 2  # Smaller size for captured pieces
        for i, piece in enumerate(self.capturedPieces["w"]):
            pieceImage = p.transform.scale(IMAGES[piece], (pieceSize, pieceSize))
            xOffset = WIDTH + 10 + (i % 4) * (pieceSize + 5)  # Move to the right
            self.screen.blit(pieceImage, (xOffset, yOffset + (i // 4) * (pieceSize + 5)))  # Move to next row

        # Draw Black Player Info (Bottom Half)
        blackTitle = titleFont.render("Black Captured Pieces", 0, p.Color("black"))
        self.screen.blit(blackTitle, (WIDTH + 10, HEIGHT - 220))

        # blackCapturedTitle = infoFont.render("", 0, p.Color("black"))
        # self.screen.blit(blackCapturedTitle, (WIDTH + 10, HEIGHT - 190))

        yOffset = HEIGHT - 180  # Start above the bottom of the sidebar
        for i, piece in enumerate(self.capturedPieces["b"]):
            pieceImage = p.transform.scale(IMAGES[piece], (pieceSize, pieceSize))
            xOffset = WIDTH + 10 + (i % 4) * (pieceSize + 5)  # Move to the right
            self.screen.blit(pieceImage, (xOffset, yOffset + (i // 4) * (pieceSize + 5)))  # Move to next row

        # Add separators between sections for clarity
        p.draw.line(self.screen, p.Color("black"), (WIDTH, 70), (WIDTH + SIDEBAR_WIDTH, 70), 2)  # Top divider
        p.draw.line(self.screen, p.Color("black"), (WIDTH, HEIGHT - 250), (WIDTH + SIDEBAR_WIDTH, HEIGHT - 250),2)  # Bottom divider

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

        image = p.image.load("images/chess2.jpg")
        image = p.transform.scale(image, (WIDTH+600, HEIGHT))  # Adjust the size as needed
        self.screen.blit(image, (WIDTH // 2 - image.get_width() // 2, HEIGHT // 2 - image.get_height() // 2))


        titleText = font.render("Black & White Team", 1, p.Color((255,255,255)))
        titleLocation = p.Rect(WIDTH // 2 - 60, HEIGHT // 2 - 200, 200, 50).move(180 - titleText.get_width() // 2,
                                                                                 25 - titleText.get_height() // 2)
        # Render the title with a shadow for better visibility
        shadow_offset = 2
        titleShadow = font.render("Black & White Team", True, (0, 0, 0))  # Black shadow
        titleText = font.render("Black & White Team", True, p.Color((168, 168, 168)))

        # Blit shadow first (offset) and then text
        self.screen.blit(titleShadow, (titleLocation.x + shadow_offset, titleLocation.y + shadow_offset))
        self.screen.blit(titleText, titleLocation)

        vsPlayerText = font.render("Player vs Player", 1, p.Color((1, 4, 41)))
        vsComputerText = font.render("Player vs Computer", 1, p.Color((1, 4, 41)))

        vsPlayerButton = p.Rect(WIDTH // 2 - vsPlayerText.get_width() // 2 + 110, HEIGHT // 2 - 70,
                                vsPlayerText.get_width() + 20, 50)
        vsComputerButton = p.Rect(WIDTH // 2 - vsComputerText.get_width() // 2 + 110, HEIGHT // 2,
                                  vsComputerText.get_width() + 20, 50)

        # Create surfaces for buttons with transparency
        vsPlayerSurface = p.Surface((vsPlayerButton.width, vsPlayerButton.height), p.SRCALPHA)
        vsComputerSurface = p.Surface((vsComputerButton.width, vsComputerButton.height), p.SRCALPHA)

        # Set transparency level (0-255, where 0 is fully transparent and 255 is fully opaque)
        transparency = 100
        vsPlayerSurface.set_alpha(transparency)
        vsComputerSurface.set_alpha(transparency)

        # Fill surfaces with color
        vsPlayerSurface.fill((230, 229, 197, transparency))
        vsComputerSurface.fill((230, 229, 197, transparency))

        # Blit surfaces onto the screen
        self.screen.blit(vsPlayerSurface, vsPlayerButton.topleft)
        self.screen.blit(vsComputerSurface, vsComputerButton.topleft)

        # Blit text onto the screen
        self.screen.blit(vsPlayerText, vsPlayerButton.move((vsPlayerButton.width - vsPlayerText.get_width()) // 2,
                                                           (vsPlayerButton.height - vsPlayerText.get_height()) // 2))
        self.screen.blit(vsComputerText,
                         vsComputerButton.move((vsComputerButton.width - vsComputerText.get_width()) // 2,
                                               (vsComputerButton.height - vsComputerText.get_height()) // 2))
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
    def ChooseLevel(self):
        font = p.font.SysFont("Helvetica", 32, True, False)

        image = p.image.load("images/chess2.jpg")
        image = p.transform.scale(image, (WIDTH+600 , HEIGHT))  # Adjust the size as needed
        self.screen.blit(image, (WIDTH // 2 - image.get_width() // 2, HEIGHT // 2 - image.get_height() // 2))

        titleText = font.render("Choose Your Level", 1, p.Color((173, 173, 173)))
        titleLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH // 2 - titleText.get_width() // 2 + 110,
                                                         HEIGHT // 4 - titleText.get_height() // 2)
        self.screen.blit(titleText, titleLocation)

        # Create surfaces for buttons with transparency
        whiteButtonSurface = p.Surface((200, 50), p.SRCALPHA)
        blackButtonSurface = p.Surface((200, 50), p.SRCALPHA)
        redButtonSurface = p.Surface((200, 50), p.SRCALPHA)

        # Set transparency level (0-255, where 0 is fully transparent and 255 is fully opaque)
        transparency = 150
        whiteButtonSurface.set_alpha(transparency)
        blackButtonSurface.set_alpha(transparency)
        redButtonSurface.set_alpha(transparency)

        # Fill surfaces with color
        whiteButtonSurface.fill((255, 255, 255, transparency))
        blackButtonSurface.fill((0, 0, 255, transparency))
        redButtonSurface.fill((255, 0, 0, transparency))

        # Define button rectangles
        whiteButton = p.Rect(WIDTH // 2 + 10, HEIGHT // 2 - 50, 200, 50)
        blackButton = p.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 20, 200, 50)
        redButton = p.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 90, 200, 50)

        # Blit surfaces onto the screen
        self.screen.blit(whiteButtonSurface, whiteButton.topleft)
        self.screen.blit(blackButtonSurface, blackButton.topleft)
        self.screen.blit(redButtonSurface, redButton.topleft)

        # Blit text onto the screen
        whiteText = font.render("Eazy", 1, p.Color("Black"))
        blueText = font.render("mid", 1, p.Color("Black"))
        radText = font.render("Hard", 1, p.Color("Black"))
        self.screen.blit(whiteText, whiteButton.move(60, 10))
        self.screen.blit(blueText, blackButton.move(60, 10))
        self.screen.blit(radText, redButton.move(60, 10))
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
                        return 2
                    elif blackButton.collidepoint(location):
                        return 3
                    elif redButton.collidepoint(location):
                        return 4
    def showColorChoiceWindow(self):
        font = p.font.SysFont("Helvetica", 32, True, False)


        image = p.image.load("images/chess2.jpg")
        image = p.transform.scale(image, (WIDTH + 600, HEIGHT))  # Adjust the size as needed
        self.screen.blit(image, (WIDTH // 2 - image.get_width() // 2, HEIGHT // 2 - image.get_height() // 2))

        titleText = font.render("Choose Your Color", 1, p.Color((173, 173, 173)))
        titleLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH // 2 - titleText.get_width() // 2 + 110, HEIGHT // 4 - titleText.get_height() // 2)
        self.screen.blit(titleText, titleLocation)


        whiteButton = p.Rect(WIDTH // 2 + 10, HEIGHT // 2 - 50, 200, 50)
        blackButton = p.Rect(WIDTH // 2 + 10, HEIGHT // 2 + 20, 200, 50)
        p.draw.rect(self.screen, p.Color("white"), whiteButton, border_radius=10)
        p.draw.rect(self.screen, p.Color("black"), blackButton, border_radius=10)

        whiteText = font.render("White", 1, p.Color("Black"))
        blackText = font.render("Black", 1, p.Color("White"))
        self.screen.blit(whiteText, whiteButton.move(60, 10))
        self.screen.blit(blackText, blackButton.move(60, 10))

        p.display.flip()
        result = None
        waiting = True
        while waiting:
            flag = 1
            for e in p.event.get():
                if e.type == p.QUIT:
                    p.quit()
                    exit()
                elif e.type == p.MOUSEBUTTONDOWN:
                    location = p.mouse.get_pos()
                    if whiteButton.collidepoint(location):
                        result =  (True , False)
                        flag = 0
                        break
                    elif blackButton.collidepoint(location):
                        result = (False, True)
                        flag = 0
                        break
            if flag == 0:
                break
        res = self.ChooseLevel()
        global depth
        depth = res
        return result

    def showPromotionChoices(self, isWhite):
        font = p.font.SysFont("Helvetica", 24, True, False)
        promotionRect = p.Rect(WIDTH + 10, HEIGHT // 2 - 100, 180, 200)
        p.draw.rect(self.screen, p.Color("lightyellow"), promotionRect)

        titleText = font.render("Promote to:", 1, p.Color("Black"))
        self.screen.blit(titleText, promotionRect.move(10, 10))

        pieces = ["Q", "R", "N", "B"]
        pieceImages = ["wQ", "wR", "wN", "wB"] if isWhite else ["bQ", "bR", "bN", "bB"]
        buttons = []
        for i, piece in enumerate(pieces):
            button = p.Rect(WIDTH + 20, HEIGHT // 2 - 50 + i * 40, 160, 30)
            p.draw.rect(self.screen, p.Color("blue"), button, border_radius=5)
            pieceImage = p.transform.scale(IMAGES[pieceImages[i]], (30, 30))
            self.screen.blit(pieceImage, button.move(10, 0))
            pieceText = font.render(piece, 1, p.Color("white"))
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