version = 'v2.6'
import re
import pypresence
import time
import psutil
import sys


def Log(msg):
    if DEBUG:
        print(f'[DEBUG] {msg}')

def HSRPC(msg):
    print(f'[HSRPC] {msg}')

def Search(*kwargs):
    return re.search(*kwargs) != None

class Discord:
    def __init__(self, Client):
        self.RichPresence = pypresence.Presence(Client)
        self.Connected = False

    def Start(self):
        self.Connect()
        
    def Connect(self):
        if self.Connected == False:
            HSRPC('Rich presence initialized!')
            self.RichPresence.connect()
            self.Connected = True
        
    def Disconnect(self):
        if self.Connected:
            self.RichPresence.close()
            self.Connected = False

    def Clear(self):
        if self.Connected:
             self.RichPresence.clear()

    def Update(self, **kwargs):
        self.RichPresence.update(**kwargs)

class Presence:
    Client = '528679932415442965'
    CLASSES = {
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
            # Classic
            'EX1_323h' : 'Warlock',
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

    GAMEMODES = {
        'GT_VS_AI' : 'Practice mode',
        'GT_RANKED' : 'Playing versus player',
        'GT_VS_FRIEND' : 'Playing versus a friend',
        'GT_TAVERNBRAWL' : 'Doing Tavern Brawl',
        'GT_TUTORIAL' : 'Doing tutorial',
        'GT_UNRANKED' : 'Playing versus player',
        'GT_ARENA' : 'Doing Arena run'
    }

    GameTypes = {
        'FT_WILD' : 'Wild',
        'FT_STANDARD' : 'Standard'
    }

    StateComplem = {
        'GT_VS_AI' : 'The Inkeeper',
        'GT_RANKED' : 'Ranked: []',
        'GT_TAVERNBRAWL' : 'Tavern Brawl',
        'GT_TUTORIAL' : 'Tutorial',
        'GT_UNRANKED' : 'Casual: []',
        'GT_ARENA' : 'Arena'
    }

    def __init__(self):
        # Rich Presence
        self.RichPresence = Discord(Presence.Client)
        self.GameEvents = []
        self.boolSpectating = False
        # Player
        self.PlayerName = None
        self.Gamemode = None
        self.Gametype = None
        self.PlayerSpectatedName = None
        self.OpponentName = None
        self.lastEvent = 0
        self.Playing = False
        self.lastMessage = None
        self.Message = None
        self.timeElapsed = None
        self.GamePID = None
        self.spammerBlock = False
        self.spammerBlocker = False
        self.PlayerID = None
        self.SpectatePlayerID = None
        self.PlayerHero = None
        self.DungeonName = None
        self.DungeonBoss = None
        self.wasSpectating = False
        self.PlayerEntity = None
        self.HeroName = None

    def SearchHearthstoneProcess(self):
        for programs in psutil.process_iter():
            if programs.name() == 'Hearthstone.exe':
                self.GamePID = programs.pid
                return
        self.GamePID = None
    
    def Stop(self):
        HSRPC('Exiting...')
        self.RichPresence.Disconnect()
        sys.exit()

    def Start(self):
        HSRPC('Initializing Hearthstone Discord Rich Presence...')
        self.RichPresence.Start()
        while True:
            self.SearchHearthstoneProcess()
            if self.GamePID == None:
                self.GameNotRunning()
                continue
            else:
                self.GameRunning()
                self.PowerLogScanner()
                self.EventsHandler()
                self.lastMessage = self.Message
                self.Message = self.GetDescriptionText()
                self.UpdatePresence()
                time.sleep(5)

    def UpdatePresence(self):
        self.RichPresence.Update(
            details = self.Message,
            state = self.SetStateText(),
            large_image = self.SetLargeImage(),
            large_text = self.HeroName if self.PlayerHero != None else 'Main Menu',
            small_image = self.SetName()[1],
            small_text = self.SetName()[0],
            start = self.timeElapsed
        )

    def SetStateText(self):
        try:
            if self.Playing or self.boolSpectating:
                if self.DungeonName != None:
                    typeGame = self.DungeonBoss
                else:
                    typeGame = Presence.StateComplem[self.Gamemode].replace('[]', Presence.GameTypes[self.Gametype])
            else:
                typeGame = None
        except Exception as e:
            Log(e)
            typeGame = None
        Log(typeGame)
        return typeGame

    def SetLargeImage(self):
        try:
            if self.Playing == False:
                if self.boolSpectating:
                    largeImage = self.PlayerHero.lower()
                else:
                    largeImage = 'menu'
            else:
                if self.PlayerHero != None and self.PlayerHero.startswith('TRLA'):
                    largeImage = 'trla_209h'
                else:
                    largeImage = self.PlayerHero.lower()
        except:
            largeImage = 'menu'
        return largeImage

    def SetName(self):
        if self.PlayerName != None:
            name = self.PlayerName.split('#')[0]
            iconimg = 'nameicon'
        else:
            name = None
            iconimg = None
        return (name, iconimg)

    def SetTimer(self):
        if self.lastMessage != self.Message or self.timeElapsed == None:
            self.timeElapsed = int(time.time())
            
    def GameRunning(self):
        if self.spammerBlocker == False:
            HSRPC('Hearthstone is open! Stablishing connection to Discord.')
            self.spammerBlocker = True
            self.spammerBlock = False

    def GameNotRunning(self):
        if self.spammerBlock == False: 
            HSRPC('Hearthstone is closed!')
            self.timeElapsed = None
            self.spammerBlock = True
            self.spammerBlocker = False
        time.sleep(5)

    def _GAMEMODE(self, name):
        return Presence.GAMEMODES[name]

    def AlreadyKnowPlayerName(self, Event):
        if self.DungeonName != None:
            self.PlayerID = '1'
        if Search(fr'PlayerName={self.PlayerName}', Event):
            self.PlayerID = re.findall(r'PlayerID=([0-2])', Event)[0]
        return

    def GetPlayerIDs(self, Event):
        return re.findall(r'id=([1-2])', Event)[0]

    def ParsePlayerName(self, Event):
        try:
            playerNameMatch = re.search(r'Player=([ a-zA-Z0-9]+)#([0-9]+)', Event).span()
            playerName = Event[playerNameMatch[0]+7 : playerNameMatch[1]]
        except:
            playerName = re.findall(r'Player=([ a-zA-Z0-9]+)', Event)[0].replace(' TaskList', '')
        return playerName

    def GetPlayerNames(self, Event):
        playerName = self.ParsePlayerName(Event)
        playerId = self.GetPlayerIDs(Event)
        if self.DungeonName != None and playerId == self.playerID:
            self.playerName = playerName
        if self.boolSpectating == False:
            self.Playing = True
            if (self.PlayerEntity == '1' and Search('CountMax=3', Event)) or playerName == self.PlayerName:
                self.PlayerID = playerId
                self.PlayerName = playerName
                Log(f'Player name: {self.PlayerName} id: {self.PlayerID} (First Player)')
            elif self.PlayerEntity == '2' and Search('CountMax=5', Event) or playerName == self.PlayerName:
                self.PlayerID = playerId
                self.PlayerName = playerName
                Log(f'Player name: {self.PlayerName} id: {self.PlayerID} (Second Player)')
            else:
                self.OpponentName = playerName
                Log(f'Opponent name: {self.OpponentName} id: {playerId}')
        else:
            if playerName != 'UNKNOWN HUMAN PLAYER' and self.PlayerSpectatedName == None:
                self.PlayerSpectatedName = playerName
            if self.PlayerSpectatedName and self.SpectatePlayerID != playerId:
                self.SpectatePlayerID = playerId
            Log(f'Spectating: {self.PlayerSpectatedName} id: {self.SpectatePlayerID}')
            self.wasSpectating = False
            self.PlayerHero = None
            self.OpponentName = None
            self.DungeonName = None

    def GetPlayerHeroMidGame(self, Event):
        cardId = re.findall(r'cardId=([a-zA-Z0-9_]+)', Event)[0]
        if cardId in Presence.CLASSES:
            self.PlayerHero = cardId
            self.GetHeroName(Event)
            Log(f'New Hero id: {self.PlayerHero}')
            Log(Event)

    def GetPlayerHero(self, Event):
        if self.boolSpectating:
            HeroId = re.findall(fr'player={self.SpectatePlayerID}] CardID=([_A-Za-z0-9]+)', Event)[0]
        else:
            HeroId = re.findall(fr'player={self.PlayerID}] CardID=([_A-Za-z0-9]+)', Event)[0]
        if HeroId.startswith('GILA'):
            self.DungeonName = 'The Witchwood'
            self.PlayerHero = HeroId
        elif HeroId.startswith('TRLA'):
            self.DungeonName = 'Rastakhan\'s Rumble'
            self.PlayerHero = HeroId
        else:
            self.PlayerHero = HeroId
        self.GetHeroName(Event)
        Log(f'Hero ID: {HeroId}')
        Log(f'Event: {Event}')

    def GetHeroName(self, Event):
        if re.search('UNKNOWN ENTITY', Event) == None:
            Log(Event)
            self.HeroName = re.findall(r'entityName=([!\',._A-Za-z0-9- *?]+) id', Event)[0]
            Log(f'Hero name: {self.HeroName}')

    def GetDescriptionText(self):
        if self.boolSpectating:
            return 'Spectating friend'
        elif self.Playing:
            if self.Gamemode == 'GT_VS_AI' and self.DungeonName != None:
                return self.DungeonName
            else:
                return f'{self._GAMEMODE(self.Gamemode)}'
        elif self.Playing == False:
            self.Gametype = None
            return 'Idle'

    def GetDungeonBossName(self, Event):
        if self.boolSpectating == False:
            self.Playing = True
        self.DungeonName = re.findall(r'entityName=([*?! ,_a-zA-Z0-9]+) id=')[0]
        Log(f'Boss: {self.DungeonName}')
        Log(Event)
        return
    
    def GetGamemode(self, Event):
        self.Gamemode = re.findall(r'GameType=([_A-Z]+)', Event)[0]
        Log(f'Gamemode: {self.Gamemode}')
        return

    def GetGameType(self, Event):
        self.Gametype = re.findall(r'FormatType=([_A-Z]+)', Event)[0]
        Log(f'Gametype: {self.Gametype}')
        return

    def Spectate(self, Event):
        if Search(r'Begin', Event):
            self.boolSpectating = True
            self.PlayerHero = None
            self.DungeonBoss = None
        elif Search(r'End', Event):
             self.wasSpectating = True
             self.boolSpectating = False   
        return

    def DetectGameOver(self, Event):
        self.Playing = False
        self.PlayerHero = None
        self.HeroName = None
        self.DungeonName = None
        Log('Game is over!')
        return

    def ResetGameEvents(self, length):
        if length < self.lastEvent:
            self.GameEvents = []
            self.lastEvent  = 0
        return

    def PowerLogScanner(self):
        try:
            PowerLog = open(r'C:\Program Files (x86)\Hearthstone\Logs\Power.log', 'r')
        except FileNotFoundError:
            HSRPC('Power.log file not found!')
            self.Stop()
        self.GameEvents = PowerLog.readlines()
        self.ResetGameEvents(len(self.GameEvents))
        PowerLog.close()

    def EventsHandler(self):
        latestEvent = self.lastEvent
        for i in range(self.lastEvent, len(self.GameEvents)):
            Event = self.GameEvents[i]
            if self.PlayerName != None and Search(r'PlayerName=', Event):
                self.AlreadyKnowPlayerName(Event)
            if self.DungeonName != None:
                self.AlreadyKnowPlayerName(Event)
            # Dungeons
                # Kobolds & Catacombs
            if Search(r'player=2] CardID=LOOTA_BOSS', Event) and Search(r'values=HERO\n', self.GameEvents[i+2]):
                self.DungeonName = 'Kobolds & Catacombs'
                self.GetDungeonBossName(Event)
                # The Boomsday Project
            if Search(r'player=2] CardID=BOTA_BOSS', Event) and Search(r'value=HERO\n', self.GameEvents[i+2]):
                self.DungeonName = 'The Boomsday Project'
                self.PlayerID = '1'
                self.GetDungeonBossName(Event)
                # Rastakhan
            if Search(r'player=2] CardID=TRLA', Event) and Search(r'value=HERO\n', self.GameEvents[i+2]):
                self.GetDungeonBossName(Event)
                # The Witchwood
            if Search(r'player=2] CardID=GILA_BOSS', Event) and Search(r'value=HERO\n', self.GameEvents[i+2]):
                self.GetDungeonBossName(Event)
                # Knights of the Frozen Throne
            if Search(r'player=2] CardID=ICC', Event) and Search(r'value=HERO\n', self.GameEvents[i+2]) and Search(r'zone=PLAY', Event):
                self.DungeonName = 'Knights of the Frozen Throne'
                self.GetDungeonBossName(Event)
            # Game events
            if Search(r'GameType=', Event):
                self.GetGamemode(Event)
            if Search(r'FormatType=', Event):
                self.GetGameType(Event)
            # Player events
            if Search(r'ChoiceType=MULLIGAN CountMin=0 CountMax=', Event):
                CountMax = int(re.findall(r'ChoiceType=MULLIGAN CountMin=0 CountMax=([0-9])', Event)[0])
                if Search(r'Entities\[4]=\[entityName=The Coin ', self.GameEvents[i+CountMax+1]):
                    self.PlayerEntity = '2'
                else:
                    self.PlayerEntity = '1'
                if Search(r'Entities\[4]=\[entityName=UNKNOWN ENTITY', self.GameEvents[i+CountMax+1]):
                    self.PlayerEntity = '1'
                else:
                    self.PlayerEntity = '2'
                self.GetPlayerNames(Event)
            if Search(r'Spectating', Event) or Search(r'Spectator Mode', Event):
                self.Spectate(Event)
            if self.boolSpectating:
                if Search(fr'player={self.SpectatePlayerID}] CardID=', Event) and Search(r'value=HERO\n', self.GameEvents[i+2]) and (Search(r'value=PLAY', self.GameEvents[i+4]) or Search(r'value=PLAY', self.GameEvents[i+5])):
                    self.GetPlayerHero(Event)
                elif Search(r'BlockType=PLAY', Event) and Search('zonePos=7', Event) and Search(fr'player={self.SpectatePlayerID}', Event):
                    self.GetPlayerHeroMidGame(Event)
            else:
                if Search(fr'player={self.PlayerID}] CardID=', Event) and Search(r'value=HERO\n', self.GameEvents[i+2]) and (Search('value=PLAY', self.GameEvents[i+4]) or Search('value=PLAY', self.GameEvents[i+5])):
                    self.GetPlayerHero(Event)
                if Search('BlockType=PLAY', Event) and Search(fr'player={self.PlayerID}', Event):
                    self.GetPlayerHeroMidGame(Event)
            if Search('TAG_CHANGE Entity=GameEntity tag=STEP value=FINAL_GAMEOVER', Event) and Search('GameState', Event):
                self.DetectGameOver(Event)
            latestEvent += 1
        self.lastEvent = latestEvent

if __name__ == '__main__':
    Presence = Presence()
    DEBUG = False
    if '--debug' in sys.argv:
        DEBUG = True
    try:
        Presence.Start()
    except KeyboardInterrupt:
        Presence.Stop()
    except pypresence.exceptions.InvalidID:
        HSRPC('Discord client id not valid! Check if Discord is open.')

