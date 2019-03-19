version = 'v2.7'
import re
import pypresence
import time
import psutil
import sys
try:
    from lib.gameStrings import Strings
    from lib.debugger import *
except ImportError:
    from gameStrings import Strings
    from debugger import *


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

    def __init__(self):
        self.HearthstonePath = r'C:\Program Files (x86)\Hearthstone\Logs\\'
        # Rich Presence
        self.RichPresence = Discord(Presence.Client)
        self.GameEvents = []
        self.MainMenuEvents = []
        self.LastEventMainMenu = 0
        self.MenuPresence = None
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
        self.InMainMenu = False

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
                if self.InMainMenu:
                    self.MainMenu()
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
                    typeGame = Strings.STATE_COMPLEM[self.Gamemode].replace('[]', Strings.GAMETYPES[self.Gametype])
            else:
                typeGame = None
        except Exception as e:
            typeGame = None
        return typeGame

    def MainMenu(self):
        self.LoadingScreenScanner()
        self.MainMenuPresence()

    def ResetMenuEvents(self, length):
        if length < self.LastEventMainMenu:
            self.MainMenuEvents = []
            self.LastEventMainMenu = 0
        return

    def LoadingScreenScanner(self):
        file = open(fr'{self.HearthstonePath}LoadingScreen.log', 'r')
        self.MainMenuEvents = file.readlines()
        self.ResetMenuEvents(len(self.MainMenuEvents))
        file.close()

    def MainMenuPresence(self):
        lastEvent = self.LastEventMainMenu
        for line in range(self.LastEventMainMenu, len(self.MainMenuEvents)):
            Event = self.MainMenuEvents[line]
            if Search('currMode', Event):
                self.ParseMenuPresence(Event)
            lastEvent += 1
        self.LastEventMainMenu = lastEvent

    def ParseMenuPresence(self, event):
        Event = re.findall(r'currMode=([_A-Z]+)\n', event)
        Log(f'Main menu event: {Event[0]}')
        self.MenuPresence = Event[0]

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
        except Exception as e:
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
            self.RichPresence.Clear()
            HSRPC('Hearthstone is closed!')
            self.timeElapsed = None
            self.spammerBlock = True
            self.spammerBlocker = False
        time.sleep(5)

    def _GAMEMODE(self, name):
        return Strings.GAMEMODES[name]

    def AlreadyKnowPlayerName(self, Event):
        if self.DungeonName != None:
            self.PlayerID = '1'
        if self.boolSpectating:
            if Search(fr'PlayerName={self.PlayerSpectatedName}', Event):
                Log(f"Spectating: {self.PlayerSpectatedName} id: {self.SpectatePlayerID}")
                self.SpectatePlayerID = re.findall(r'PlayerID=([0-2])', Event)[0]
                return
        else:
            if Search(fr'PlayerName={self.PlayerName}', Event):
                self.PlayerID = re.findall(r'PlayerID=([0-2])', Event)[0]
                self.Playing = True
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
        if self.DungeonName != None and playerId == self.PlayerID:
            self.playerName = playerName
        if self.boolSpectating == False:
            self.Playing = True
            if (self.PlayerEntity == '1' and Search('CountMax=5', Event)) or playerName == self.PlayerName:
                self.OpponentName = playerName
                Log(f'Opponent name: {self.OpponentName} id: {playerId}')
            elif self.PlayerEntity == '2' and Search('CountMax=5', Event) or playerName == self.PlayerName:
                self.PlayerID = playerId
                self.PlayerName = playerName
                Log(f'Player name: {self.PlayerName} id: {self.PlayerID} (Second Player)')
            else:
                self.PlayerID = playerId
                self.PlayerName = playerName
                Log(f'Player name: {self.PlayerName} id: {self.PlayerID}')
        else:
            if (self.PlayerEntity == '1' and Search('CountMax=5', Event)) and self.PlayerSpectatedName != None:
                self.OpponentName = playerName
                Log(f'Opponent: {self.OpponentName} id: {playerId}')
            elif self.PlayerEntity == '2' and Search('CountMax=5', Event) and self.PlayerSpectatedName != None:
                self.SpectatePlayerID = playerId
                self.PlayerSpectatedName = playerName
                Log(f'Spectating: {self.PlayerSpectatedName} id: {self.SpectatePlayerID}')
            else:
                self.SpectatePlayerID = playerId
                self.PlayerSpectatedName = playerName
                Log(f'Spectating: {self.PlayerSpectatedName} id: {self.SpectatePlayerID}')
            self.wasSpectating = False

    def GetPlayerHeroMidGame(self, Event):
        try:
            cardId = re.findall(r'cardId=([a-zA-Z0-9_]+)', Event)[0]
        except:
            return
        if cardId in Strings.HERO:
            self.PlayerHero = cardId
            self.GetHeroName(Event)
            Log(f'New Hero id: {self.PlayerHero}')
            #Log(Event)

    def GetPlayerHero(self, Event):
        if self.boolSpectating:
            HeroId = re.findall(fr'player={self.SpectatePlayerID}] CardID=([_A-Za-z0-9]+)', Event)[0]
        else:
            HeroId = re.findall(fr'player={self.PlayerID}] CardID=([_A-Za-z0-9]+)', Event)[0]
        if HeroId.startswith('GILA'):
            self.DungeonName = 'The Witchwood'
            self.PlayerHero = HeroId
        elif HeroId.startswith('TRLA') and self.Gamemode == 'GT_VS_AI':
            self.DungeonName = 'Rastakhan\'s Rumble'
            self.PlayerHero = HeroId
        else:
            self.PlayerHero = HeroId
        self.GetHeroName(Event)
        Log(f'Hero ID: {HeroId}')
        #Log(f'Event: {Event.strip('\n')}')

    def GetHeroName(self, Event):
        if re.search('UNKNOWN ENTITY', Event) == None:
            #Log(Event)
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
            self.InMainMenu = True
            self.Gametype = None
            self.MainMenu()
            try:
                Message = Strings.PRESENCE_MESSAGES[self.MenuPresence]
            except KeyError:
                Log(f'MENU EVENT NOT MAPPED YET: {self.MenuPresence}')
                Message = Strings.PRESENCE_MESSAGES['HUB']
            return Message

    def GetDungeonBossName(self, Event):
        if self.boolSpectating == False:
            self.Playing = True
        #Log(Event)
        self.DungeonBoss = re.findall(r'entityName=([*?! ,_a-zA-Z0-9]+) id=', Event)[0]
        Log(f'Boss: {self.DungeonBoss}')
        
        return
    
    def GetGamemode(self, Event):
        self.Gamemode = re.findall(r'GameType=([_A-Z]+)', Event)[0]
        Log('=== NEW GAME ===')
        self.InMainMenu = False
        Log(f'Gamemode: {self.Gamemode}')
        return

    def GetGameType(self, Event):
        self.Gametype = re.findall(r'FormatType=([_A-Z]+)', Event)[0]
        Log(f'Gametype: {self.Gametype}')
        return

    def Spectate(self, Event):
        if Search(r'Begin', Event):
            Log("BEGIN SPECTATING")
            self.boolSpectating = True
            self.PlayerHero = None
            self.DungeonBoss = None
            self.PlayerEntity = None
        elif Search(r'End', Event):
            Log("END SPECTATING")
            self.wasSpectating = True
            self.boolSpectating = False
            self.PlayerEntity = None
        return

    def DetectGameOver(self, Event):
        self.Playing = False
        self.PlayerHero = None
        self.HeroName = None
        self.DungeonName = None
        Log('Game is over!\n')
        return

    def ResetGameEvents(self, length):
        if length < self.lastEvent:
            self.GameEvents = []
            self.lastEvent  = 0
        return

    def PowerLogScanner(self):
        try:
            PowerLog = open(fr'{self.HearthstonePath}Power.log', 'r')
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
            if self.boolSpectating and self.PlayerSpectatedName != None and Search('PlayerName=', Event):
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
            if Search(r'player=2] CardID=TRLA', Event) and self.Gamemode == 'GT_VS_AI' and Search(r'value=HERO\n', self.GameEvents[i+2]):
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
            if Search(r'ChoiceType=MULLIGAN CountMin=0 CountMax=', Event) and self.PlayerEntity == None:
                CountMax = int(re.findall(r'ChoiceType=MULLIGAN CountMin=0 CountMax=([0-9])', Event)[0])
                if CountMax == 5 and Search(r'Entities\[4]=\[entityName=The Coin', self.GameEvents[i+CountMax+1]):
                    self.PlayerEntity = '2'
                elif CountMax == 5 and Search(r'Entities\[4]=\[entityName=UNKNOWN ENTITY', self.GameEvents[i+CountMax+1]):
                    self.PlayerEntity = '1'
                else:
                    self.PlayerEntity = None
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
    config.DEBUG = False
    if '--debug' in sys.argv:
        config.DEBUG = True
    try:
        Presence.Start()
    except KeyboardInterrupt:
        Presence.Stop()
    except pypresence.exceptions.InvalidPipe:
        HSRPC('Discord client id not valid! Check if Discord is open.')
