version = 'v2.6'
import re
import pypresence
import time
import psutil
import sys

debug = False

classes = {
            # Normal Heroes
            'HERO_01' : 'Warrior',
            'HERO_02' : 'Shaman',
            'HERO_03' : 'Rogue',
            'HERO_04' : 'Paladin',
            'HERO_05' : 'Hunter',
            'HERO_06' : 'Druid',
            'HERO_07' : 'Warlock',
            'HERO_08' : 'Mage',
            'HERO_09' : 'Priest',
            # Knights of the frozen throne expansion
            'ICC_827' : 'Rogue',
            'ICC_828' : 'Hunter',
            'ICC_829' : 'Paladin',
            'ICC_830' : 'Priest',
            'ICC_831' : 'Warlock',
            'ICC_832' : 'Druid',
            'ICC_833' : 'Mage',
            'ICC_834' : 'Warrior',
            'ICC_481' : 'Shaman',
            # The boomsday project Heroes
            'BOT_238' : 'Warrior',
            # The Witchwood Heroes
            'GIL_504' : 'Shaman',
            'GILA_500h3' : 'Tracker',
            'GILA_600h' : 'Cannoneer',
            'GILA_400h' : 'Houndmaster',
            'GILA_900h' : 'Time-Tinker',
            # Rastakhan Heroes
            'TRL_065' : 'Hunter',
            None : 'Playing Hearthstone'
        }

gameTypes = {
    'FT_WILD' : 'Wild',
    'FT_STANDARD' : 'Standard'
}

stateComplem = { 
    'GT_VS_AI' : 'The Inkeeper',
    'GT_RANKED' : 'Ranked: []',
    'GT_TAVERNBRAWL' : 'Tavern Brawl',
    'GT_TUTORIAL' : 'Tutorial',
    'GT_UNRANKED' : 'Casual: []',
    'GT_ARENA' : 'Arena'
}

gameModes = {
    'GT_VS_AI' : 'Practice mode',
    'GT_RANKED' : 'Playing versus player',
    'GT_VS_FRIEND' : 'Playing versus a friend',
    'GT_TAVERNBRAWL' : 'Doing Tavern Brawl',
    'GT_TUTORIAL' : 'Doing tutorial',
    'GT_UNRANKED' : 'Playing versus player',
    'GT_ARENA' : 'Doing Arena run'
}

images = {
    'GT_VS_AI' : 'normal',
    'GT_RANKED' : 'normal',
    'GT_VS_FRIEND' : 'normal',
    'GT_TAVERNBRAWL' : 'brawl',
    'GT_TUTORIAL' : 'normal',
    'GT_UNRANKED' : 'normal',
    'GT_ARENA' : 'arena'
}

clientID = '528679932415442965'

# Debug function
def Log(msg):
    if debug:
        print(f'[DEBUG] {msg}')

class richPresence:
    def __init__(self, clientId):
        self.RPC = pypresence.Presence(clientId)
        self.connected = False

    def start(self):
        self.connect()

    def clear(self):
        if self.connected:
            self.RPC.clear()

    def connect(self):
        if self.connected == False:
            print('[HSRPC] Rich presence initialized.')
            self.RPC.connect()
            self.connected = True

    def disconnect(self):
        if self.connected:
            self.RPC.close()
            self.connected = False

    def update(self, **kwargs):
        self.RPC.update(**kwargs)


class HearthstoneRPC:
    def __init__(self):
        self.rpc = richPresence(clientID)
        self.rpc.start()
        self.log = None # Hearthstone Log
        self.spectating = False # True if user is spectating, False if not
        self.gamemode = None # Game mode (e.g: Player vs AI, Player vs Player, Player vs Friend)
        self.type = None # Game type (e.g: Standart/Wild)
        self.playerSpectated = None # Player user is spectating
        self.playerName = None # Player name
        self.opponentName = None # Opponent name
        self.lastLine = 0 # Last line read by the program
        self.playing = False # If player is in a match
        self.lastMessage = None # Last message generated by format_message
        self.message = None # Message generated by format_message
        self.timer = None # Time elapsed
        self.gamePID = None # Hearthstone pid
        self.pids = []  # PIDs of programs
        self.spammerBlock = False # Blocks repetitive messages
        self.spammerBlocker = False # Blocks other repetitive messages 
        self.playerID = None   # Player id (1 if first player and 2 if second player)
        self.spectatePlayerID = 0 # Same as playerID but for the spectated player
        self.playerClass = None # Player class card name
        self.dungeonName = None # Dungeon name
        self.dungeonBoss = None # Dungeon boss name
        self.wasSpectating = False # if player was spectating someone
        self.playerEntity = None # Player Entity, used to detect if player is first or second in the match

    def stop(self):
        '''Function to stop RPC when main loop is stopped by user'''
        print('[HSRPC] Exiting...')
        self.rpc.disconnect()
        sys.exit()

    def start(self):
        '''Function to start the main loop'''
        print('[HSRPC] Initializing Hearthstone Discord rich presence...')
        while True:
            self.pidScanner()
            if self.gamePID in self.pids:
                self.rpc.clear()
                if self.spammerBlocker == False:
                    print('[HSRPC] Hearthstone is closed!')
                    self.timer = None # Resets timer
                    self.spammerBlocker = True
                    self.spammerBlock = False
                time.sleep(5)
                continue
            if self.spammerBlock == False:
                print('[HSRPC] Hearthstone is open! Stablishing connection to discord.')
                self.spammerBlock = True
                self.spammerBlocker = False
            self.rpc.start()
            self.gameScanner()
            self.events()
            self.lastMessage = self.message
            self.message = self.formatDescriptionMessage()
            if self.playerName != None:
                name = self.playerName.split('#')[0]
                iconimg = 'nameicon'
            else:
                name = None
                iconimg = None
            try:
                if self.playing or self.spectating:
                    if self.dungeonName != None:
                        typeGame = self.dungeonBoss
                    else:
                        typeGame = stateComplem[self.gamemode].replace('[]', gameTypes[self.type])
                else:
                    typeGame = None
            except Exception as e:
                typeGame = None
            try:
                if self.playing == False:
                    if self.spectating:
                        largeImage = self.playerClass.lower()
                    else:
                        largeImage = 'menu'
                else:
                    if self.playerClass != None and self.playerClass.startswith('TRLA'):
                        largeImage = 'trla_209h'
                    else:
                        largeImage = self.playerClass.lower()
            except Exception as e:
                largeImage = 'menu'
            if self.lastMessage != self.message or self.timer == None:
                self.timer = int(time.time())
            self.rpc.update(
                details=self.message, 
                state=typeGame, 
                large_image=largeImage, 
                large_text = self.getClassName(),
                small_image=iconimg,
                small_text= name,
                start=self.timer)
            time.sleep(5)

    def search(self, *args):
        return re.search(*args) != None

    def pidScanner(self):
        '''Function to scan all processes searching for the Hearthstone.exe'''
        for programs in psutil.process_iter():
            if programs.pid not in self.pids:
                self.pids.append(programs.pid)
            if programs.name() == 'Hearthstone.exe':
                self.gamePID = programs.pid
                return
            else:
                self.gamePID = None 

    def formatDescriptionMessage(self):
        '''Function to format the rich presence description based on game mode'''
        if self.spectating:
            return 'Spectating friend'
        elif self.playing:
            if self.gamemode == 'GT_VS_AI' and self.dungeonName != None:
                return self.dungeonName
            else:
                return f'{gameModes[self.gamemode]}'
        elif self.playing == False:
            self.type = None
            return 'Idle'
    
    def resetLogger(self, length):
        '''Function to reset the variable that stores the game log, 
            used to fix the logger when the log is restarted'''
        if length < self.lastLine:
            self.log = []
            self.lastLine = 0

    def gameScanner(self):
        '''Function to scan Power.log and update it's variable'''
        try:
            logger = open(r'C:\Program Files (x86)\Hearthstone\Logs\Power.log', 'r')
        except FileNotFoundError:
            print('[HSRPC] Power.log file not found!')
            self.stop()
        self.log = logger.readlines()
        self.resetLogger(len(self.log))
        logger.close()
    
    def events(self):
        '''Function to scan for game events and update rich presence core variables'''
        lastIndex = self.lastLine
        for lineIndex in range(self.lastLine, len(self.log)):
            line = self.log[lineIndex]
            if self.playerName != None and self.search(r'PlayerName=', line):
                self.alreadyKnowPlayerName(line)
            if self.search(r'player=2] CardID=LOOTA_BOSS', line) and self.search(r'value=HERO\n', self.log[lineIndex+2]): # Kobolds and Catacombs
                self.dungeonName = 'Kobolds & Catacombs'
                self.getBossName(line)
            if self.search(r'player=2] CardID=BOTA_BOSS', line) and self.search(r'value=HERO\n', self.log[lineIndex+2]): # The Boomsday Project
                self.dungeonName = 'The Boomsday Project'
                self.playerID = '1'
                self.getBossName(line)
            if self.search(r'player=2] CardID=TRLA', line) and self.search(r'value=HERO\n', self.log[lineIndex+2]): # Rastakhan
                self.getBossName(line)
            if self.search(r'player=2] CardID=GILA_BOSS', line) and self.search(r'value=HERO\n', self.log[lineIndex+2]): # The Witchwood
                self.getBossName(line)
            if self.search(r'player=2] CardID=ICC', line) and self.search(r'value=HERO\n', self.log[lineIndex+2]) and self.search(r'zone=PLAY', line): # Knights of the frozen throne
                self.dungeonName = 'Knights of the Frozen Throne'
                self.getBossName(line)
            if self.search(r'GameType=', line):
                self.getGamemode(line)
            if self.search(r'FormatType=', line):
                self.getGameType(line)
            if self.search(r'ChoiceType=MULLIGAN CountMin=0 CountMax=', line):
                CountMax = int(re.findall(r'ChoiceType=MULLIGAN CountMin=0 CountMax=([0-9])', line)[0])
                if self.search(r'Entities\[4]=\[entityName=The Coin ', self.log[lineIndex+CountMax+1]):
                    self.playerEntity = '2'
                else:
                    self.playerEntity = '1'
                if self.search(r'Entities\[4]=\[entityName=UNKNOWN ENTITY', self.log[lineIndex+CountMax+1]):
                    self.playerEntity = '1'
                else:
                    self.playerEntity = '2'
                self.getPlayerNames(line)
            if self.search(r'Spectating', line) or self.search(r'Spectator Mode', line):
                self.spectate(line)
            if self.spectating:
                if self.search(fr'player={self.playerID}] CardID=', line) and self.search(r'value=HERO\n', self.log[lineIndex+2]) and (self.search(r'value=PLAY', self.log[lineIndex+4]) or self.search(r'value=PLAY', self.log[lineIndex+5])):
                    self.getPlayerHero(line)
                elif self.search(fr'BlockType=PLAY', line) and self.search('zonePos=7', line) and self.search(fr'player={self.playerID}', line):
                    self.getPlayerHeroMidGame(line)
            else:
                if self.search(fr'player={self.playerID}] CardID=', line) and self.search(r'value=HERO\n', self.log[lineIndex+2])  and (self.search(r'value=PLAY', self.log[lineIndex+4]) or self.search(r'value=PLAY', self.log[lineIndex+5])):
                    self.getPlayerHero(line)
                    print(line)
                if self.search(fr'BlockType=PLAY', line) and self.search(fr'player={self.playerID}', line):
                    self.getPlayerHeroMidGame(line)
            if self.search(r'tag=STEP value=FINAL_GAMEOVER', line):
                self.detectGameOver(line)
            lastIndex += 1
        self.lastLine = lastIndex

    def getBossName(self, line):
        '''Function to get the boss name using regular expressions'''
        if self.spectating == False:
            self.playing = True
        index = re.search(r'entityName=', line).span()[1]
        for letter in range(len(line)):
            if line[letter+2:letter+5] == 'id=':
                self.dungeonBoss = line[index:letter+1]
                break
        Log(f'BOSS: {self.dungeonBoss}')
        Log(line)

    def getGamemode(self, line):
        '''Function to get game mode using regular expressions'''
        index = re.search(r'GameType=', line).span()[1]
        maxIndex = len(line)
        self.gamemode = line[index : maxIndex].strip('\n')
        return

    def getGameType(self, line):
        '''Function to get game type using regular expressions'''
        index = re.search(r'FormatType=', line).span()[1]
        maxIndex = len(line)
        self.type = line[index : maxIndex].strip('\n')
        return

    def spectate(self, line):
        '''Function to check if the player is spectating someone'''
        if re.search(r'Begin', line) != None:
            index = re.search(r'Begin Spectating', line).span()[1]+1
            maxIndex = index+3
            self.spectating = True
            self.playerClass = None
            self.dungeonBoss = None
        elif re.search(r'End', line):
            self.wasSpectating = True
            self.spectating = False
        return

    def detectGameOver(self, line):
        '''Function that tells when the game is over'''
        self.playing = False
        self.playerClass = None
        self.dungeonName = None
        Log('Game is over!')
        return

    def alreadyKnowPlayerName(self, line):
        if self.search(fr'PlayerName={self.playerName}', line):
            self.playerID = re.findall(r'PlayerID=([0-2])', line)[0]


    def getPlayerNames(self, line):
        '''Function to get player name'''
        try:
            playerNameMatch = re.search(r'Player=([ a-zA-Z0-9]+)#([0-9]+)', line).span()
            playerName = line[playerNameMatch[0]+7 : playerNameMatch[1]]
        except:
            playerName = re.findall(r'Player=([ a-zA-Z0-9]+)', line)[0].replace(' TaskList', '')
        playerId = re.findall(r'id=([1-2])', line)[0]
        if self.spectating == False:
            self.playing = True
            if self.playerEntity == '1' and self.search('CountMax=3', line): # First player
                self.playerID = playerId
                self.playerName = playerName
                Log(f'Player name: {self.playerName} id: {self.playerID} (First player)')
            elif self.playerEntity == '2' and self.search('CountMax=5', line): # Second player
                self.playerID = playerId
                self.playerName = playerName
                Log(f'Player name: {self.playerName} id: {self.playerID} (Second player)')
            else:
                self.opponentName = playerName
                Log(f'Opponent name: {self.opponentName} id: {playerId}')
        else:
            if playerName != 'UNKNOWN HUMAN PLAYER' and self.playerSpectated == None:
                self.playerSpectated = playerName
            if self.playerSpectated == playerName and self.spectatePlayerID != playerId:
                self.spectatePlayerID = playerId
            Log(f'Spectating: {self.playerSpectated} | [{self.spectatePlayerID}]')
            self.wasSpectating = False
            self.playerClass = None
            self.opponentName = None
            self.dungeonName = None

    def getPlayerHeroMidGame(self, line):
        cardId = re.findall(r'cardId=([a-zA-Z0-9_]+)', line)[0]
        if cardId in classes:
            self.playerClass = cardId
            Log(f'New Hero id: {self.playerClass}')
            Log(line)

    def getPlayerHero(self, line):
        '''Function to get player hero id'''
        if self.spectating:
            index = re.search(fr'player={self.spectatePlayerID}] CardID=', line).span()[1]
        else:
            index = re.search(fr'player={self.playerID}] CardID=', line).span()[1]
        cardName = line[index : len(line)].strip('\n')
        if cardName.startswith('GILA'):
            self.dungeonName = 'The Witchwood'
            self.playerClass = cardName
        elif cardName.startswith('TRLA'):
            self.dungeonName = 'Rastakhan\'s Rumble'
            self.playerClass = cardName
        else:
            self.playerClass = cardName
        Log(f'Hero ID: {cardName}')
        Log(f'Line: {line}')

    def getClassName(self):
        '''Function that replaces hero id with the actual hero class'''
        if self.playerClass != None and self.playerClass.startswith('TRLA'): # Rastakhan work around
            return f'{self.playerClass.split("_")[2]}'
        if self.playerClass != None:
            return classes[self.playerClass]
        else:
            return classes[self.playerClass]

if __name__ == '__main__':
    rpc = HearthstoneRPC()
    if '--debug' in sys.argv:
        debug = True
    try:
        rpc.start()
    except KeyboardInterrupt:
        rpc.stop()
    except pypresence.exceptions.InvalidID:
        print('[HSRPC] Discord client id not valid! Check if Discord is open.')
