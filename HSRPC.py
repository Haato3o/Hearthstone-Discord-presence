import re
import pypresence
import time
import psutil
import sys

debug = False

gameTypes = {
    'FT_WILD' : 'Wild',
    'FT_STANDARD' : 'Standard'
}

stateComplem = { 
    'GT_VS_AI' : 'Dungeon',
    'GT_RANKED' : 'Ranked: []',
    'GT_TAVERNBRAWL' : 'Tavern Brawl',
    'GT_TUTORIAL' : 'Tutorial',
    'GT_UNRANKED' : 'Casual: []',
    'GT_ARENA' : 'Arena'
}

gameModes = {
    'GT_VS_AI' : 'Playing versus AI',
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
        self.lastLine = 0 # Last line read
        self.playing = False # If player is in a match
        self.lastMessage = None # Last message generated by format_message
        self.message = None # Message generated by format_message
        self.timer = None # Time elapsed
        self.gamePID = None # Hearthstone pid
        self.pids = []
        self.spammerBlock = False # Blocks repetitive messages
        self.spammerBlocker = False # Blocks other repetitive messages 
        self.playerID = 1
        self.playerClass = None
        self.dungeonName = None

    def stop(self):
        print('[HSRPC] Exiting...')
        self.rpc.disconnect()
        sys.exit()

    def start(self):
        print('[HSRPC] Initializing Hearthstone Discord rich presence...')
        while True:
            self.scan_pids()
            if self.gamePID not in self.pids:
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
            self.scan_log()
            self.reader()
            self.lastMessage = self.message
            self.message = self.format_messages()
            try:
                if self.playing or self.spectating:
                    typeGame = stateComplem[self.gamemode].replace('[]', gameTypes[self.type])
                else:
                    typeGame = None
            except:
                typeGame = None
            try:
                if self.playing == False:
                    largeImage = 'menu'
                else:
                    largeImage = self.playerClass.lower()
            except:
                largeImage = 'hearthstonelogo'
            if self.lastMessage != self.message:
                self.timer = int(time.time())
            self.rpc.update(
                details=self.message, 
                state=typeGame, 
                large_image=largeImage, 
                large_text = self.get_class_name(),
                small_image='usericon_white',
                small_text=self.playerName.split('#')[0],
                start=self.timer)
            time.sleep(15)

    def scan_pids(self):
        for programs in psutil.process_iter():
            if programs.pid not in self.pids:
                self.pids.append(programs.pid)
            if programs.name() == 'Hearthstone.exe':
                self.gamePID = programs.pid
                return
            else:
                self.gamePID = None 

    def format_messages(self):
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
    
    def fix_logger(self, length):
        if length < self.lastLine:
            self.lastLine = 0

    def scan_log(self):
        try:
            logger = open(r'C:\Program Files (x86)\Hearthstone\Logs\Power.log', 'r')
        except FileNotFoundError:
            print('[HSRPC] Power.log file not found!')
            self.stop()
        self.log = logger.readlines()
        self.fix_logger(len(self.log))
        logger.close()
    
    def reader(self):
        lastIndex = self.lastLine
        for lineIndex in range(self.lastLine, len(self.log)):
            line = self.log[lineIndex]
            if re.search(r'GameType=', line) != None:
                self.get_gamemode(line)
            if re.search(r'FormatType=', line) != None:
                self.get_type(line)
            if re.search(r'PlayerName=', line) != None:
                self.get_player_names(line)
            if re.search(r'Spectating', line) != None or re.search(r'Spectator Mode', line) != None:
                self.spectate(line)
            if re.search(fr'player={self.playerID}] CardID=', line) != None and re.search(r'value=HERO_POWER', self.log[lineIndex+2]) == None:
                self.get_player_hero(line)
            if re.search(r'value=FINAL_GAMEOVER', line) != None:
                self.detect_end(line)
            lastIndex += 1
        self.lastLine = lastIndex

    def get_gamemode(self, line):
        index = re.search(r'GameType=', line).span()[1]
        maxIndex = len(line)
        self.gamemode = line[index : maxIndex].strip('\n')
        return

    def get_type(self, line):
        index = re.search(r'FormatType=', line).span()[1]
        maxIndex = len(line)
        self.type = line[index : maxIndex].strip('\n')
        return

    def spectate(self, line):
        if re.search(r'Begin', line) != None:
            index = re.search(r'Begin Spectating', line).span()[1]+1
            maxIndex = index+3
            self.spectating = True
        elif re.search(r'End', line):
            self.spectating = False
        return

    def detect_end(self, line):
        self.playing = False
        self.playerClass = None
        return

    def get_player_names(self, line):
        index = re.search(r'PlayerName=', line).span()[1]
        maxIndex = len(line)
        if self.spectating == False:
            self.playing = True
            self.playerSpectated = None
            if self.playerName == None:
                self.playerName = line[index : maxIndex].strip('\n')
            if line[index : maxIndex].strip('\n') == self.playerName:
                self.playerID = line[re.search(r'PlayerID=', line).span()[1]]
            elif line[index : maxIndex].strip('\n') != 'The Inkeeper':
                self.opponentName = line[index : maxIndex].strip('\n')
                self.dungeonName = None
        else:
            if line[index:maxIndex].strip('\n') != 'UNKNOWN HUMAN PLAYER' and self.playerSpectated == None:
                self.playerSpectated = line[index:maxIndex]
            self.opponentName = None
            self.dungeonName = None

    def get_player_hero(self, line):
        index = re.search(fr'player={self.playerID}] CardID=', line).span()[1]
        cardName = line[index : len(line)].strip('\n')
        if cardName.startswith('HERO'):
            self.playerClass = cardName
        elif cardName.startswith('GILA'): # The witchwood dungeon
            self.dungeonName = 'The Witchwood'
            self.playerClass = cardName 
        if debug: print(self.playerClass)

    def get_class_name(self):
        classes = {
            'HERO_01' : 'Playing as Warrior',
            'HERO_02' : 'Playing as Shaman',
            'HERO_03' : 'Playing as Rogue',
            'HERO_04' : 'Playing as Paladin',
            'HERO_05' : 'Playing as Hunter',
            'HERO_06' : 'Playing as Druid',
            'HERO_07' : 'Playing as Warlock',
            'HERO_08' : 'Playing as Mage',
            'HERO_09' : 'Playing as Priest',
            'GILA_500h3' : 'Playing as Tracker',
            'GILA_600h' : 'Playing as Cannoneer',
            'GILA_400h' : 'Playing as Houndmaster',
            'GILA_900h' : 'Playing as Time-Tinker',
            None : 'Playing Hearthstone'
        }
        if self.playerClass != None and self.dungeonName == None:
            return classes[self.playerClass[0:7]]
        elif self.playerClass != None and self.dungeonName != None:
            return classes[self.playerClass]
        else:
            return classes[self.playerClass]

if __name__ == '__main__':
    rpc = HearthstoneRPC()
    try:
        rpc.start()
    except KeyboardInterrupt:
        rpc.stop()
    
