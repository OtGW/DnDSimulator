from Ifstatement_class import ifstatements
from random import random
from Entity_class import * #should be disabled before running
from Token_class import *

class spell:
    def __init__(self, player):
        #this class is initiated at the entity for spellcasting
        self.DM = player.DM
        self.player = player            #the Player that is related to this spell Object and which will cast this spell
        self.TM = self.player.TM       #Token Manager of player 
        if self.player.DM.AI_blank: #this is only a dirty trick so that VScode shows me the attributes of player and MUST be deactived, AI_blank should be false
            self.player = entity('test', 0, 0)


        #Initial
        if hasattr(self, 'spell_name') == False:
            self.spell_name = 'undefined'          #Give Name, if not specified in subclass
        if hasattr(self, 'spell_text') == False:
            self.spell_text = 'undefined'         #This is the text name that will be printed

        self.spell_level = 0
        self.cast_level = 0 #Will be set before every cast
        self.spell_save_type = False        #Type of the Spell Save 
        self.is_bonus_action_spell = False
        self.is_concentration_spell = False
        self.is_reaction_spell = False
        self.is_cantrip = False
        self.is_twin_castable = False      #Meta Magic Option
        self.is_range_spell = False

        #Activate the Spell, if the player knows it
        self.is_known = False
        if self.spell_name in player.spell_list:
            self.is_known = True

        self.was_cast = 0

    #any spell has a specific Spell cast function that does what the spell is supposed to do
    #This Function is the cast function and will be overwritten in the subclasses
    #To do so, the make_spell_check function makes sure, that everything is in order for the self.player to cast the spell
    #The make_action_check function checks if Action, Bonus Action is used
    #the spell class objects will be linked to the player casting it by self.player

    def cast(self, targets, cast_level = False, twinned = False):
        if cast_level == False: cast_level = self.spell_level
        self.autorize_cast(cast_level)
        self.announce_cast()

    def autorize_cast(self, cast_level):
        #Checks if cast is autorized
        #Make a check if cast is possible
        if cast_level == False:
            cast_level = self.spell_level #cast as level if nothing else

        if self.is_cantrip:
            if self.make_cantrip_check() == False:
                return
        else:
            if self.make_spell_check(cast_level=cast_level) == False:
                return
        
        #If everything is autorized, set cast_level
        self.cast_level = cast_level
        self.was_cast += 1  #for spell recap

    def announce_cast(self):
        self.player.DM.say(self.player.name + ' casts ' + self.spell_text + ' at lv.' + str(self.cast_level))

    def score(self, fight, twinned_cast = False):
        #The Score function is called in the Choices Class
        #It is supposed to return a dmg equal score
        #It also returns the choosen SpellTargts and the CastLevel
        #If this spell is not soposed to be considered as an option this turn, return 0 score
        #This function should be overwritten in the subclassses
        self.return_0_score()

    def make_spell_check(self, cast_level):
        #This function also sets the action, reaction or bonus action ans spell counter down
        rules = [self.is_known, 
                self.player.raged == 0,
                cast_level >= self.spell_level, 
                self.player.spell_slot_counter[cast_level -1] > 0,
                self.player.wild_shape_HP == 0,
                self.is_concentration_spell == False or self.player.is_concentrating==False]
        errors = [self.player.name + ' tried to cast ' + self.spell_name + ', without knowing the spell',
                self.player.name + ' tried to cast ' + self.spell_name + ' but is raging',
                self.player.name + ' tried to cast ' + self.spell_name + ' at a lower level: ' + str(cast_level),
                self.player.name + ' tried to cast ' + self.spell_name +', but spell slots level ' + str(cast_level) + ' are empty',
                self.player.name + ' tried to cast ' + self.spell_name + ', but is in wild shape',
                self.player.name + ' tried to cast ' + self.spell_name + ', but is currently concentrating']
        ifstatements(rules, errors, self.DM).check()

        #Is reaction Spell break here
        if self.is_reaction_spell:
            if self.player.reaction == 0:
                self.DM.say(self.player.name + ' tired to cast ' + self.spell_name + ', but hast no reaction')
                quit()
            else:
                self.player.reaction = 0
                self.player.spell_slot_counter[cast_level-1] -= 1   #one SpellSlot used
                return True
        #check if player has cast this round
        elif self.player.cast == 0:
            self.DM.say(self.player.name + ' tried to cast ' + self.spell_name + ', but has already cast a spell')
            quit()
        #check is player has action/bonus action left
        elif self.make_action_check() == False:
            quit()
        #everything clear for cast
        else:
            self.player.spell_slot_counter[cast_level-1] -= 1   #one SpellSlot used
            return True

    def make_cantrip_check(self):
        rules = [self.is_known,
                self.player.raged == 0,
                self.player.wild_shape_HP == 0,
                self.is_concentration_spell == False or self.player.is_concentrating==False]
        errors = [self.player.name + ' tried to cast ' + self.spell_name + ', without knowing the spell',
                self.player.name + ' tried to cast ' + self.spell_name + ' but is raging',
                self.player.name + ' tried to cast ' + self.spell_name + ', but is in wild shape',
                self.player.name + ' tried to cast ' + self.spell_name + ', but is currently concentrating']
        ifstatements(rules, errors, self.DM).check()
        #check is player has action/bonus action left
        if self.make_action_check() == False:
            quit()
        #everything clear for cast
        else:
            return True        

    def make_action_check(self):
        #This function checks is the player has the required action left and sets it off if so
        #Bonus Action Spell
        if self.is_bonus_action_spell:
            #Bonus Action used?
            if self.player.bonus_action == 0:
                self.DM.say(self.player.name + ' tried to cast ' + self.spell_name + ', but has no Bonus Action left')
                quit()
            #Allow cast and use bonus_action
            else:
                self.player.bonus_action = 0       #Bonus Action used
                if self.is_cantrip == False:
                    self.player.cast = 0
                return True
            
        #Action Spell
        else:
            #Quickened Spell
            if self.player.quickened_spell == 1:
                #Bonus Action free?
                if self.player.bonus_action == 1:
                    #Cast Spell as quickened BA
                    self.player.bonus_action = 0
                    self.player.quickened_spell = 0
                    if self.is_cantrip == False:
                        self.player.cast = 0
                    return True
                #No Bonus Action left
                else:
                    self.DM.say(self.player.name + ' tried to quickened cast ' + self.spell_name + ', but has no Bonus Action left')
                    quit()
            #No Quickened Spell
            else:
                if self.player.action == 0:
                    self.DM.say(self.player.name + ' tried to cast ' + self.spell_name + ', but has no action left')
                    return False
                else:
                    self.player.action = 0  #action used
                    if self.is_cantrip == False:
                        self.player.cast = 0
                    return True

#-------------Meta Magic------------------
    #The mega magic functions do their job and then cast the individual spell
    #See cast function in subclasses
    #the twin_cast function needs exectly two targets
    def twin_cast(self, targets, cast_level=False):
        rules = [len(targets)==2,
                self.player.knows_twinned_spell,
                self.player.sorcery_points >= 2]
        errors = [self.player.name + ' tried to twinned spell ' + self.spell_name + ' but not with 2 targets',
                self.player.name + ' tried to twinned cast ' + self.spell_name + ' without knwoing it',
                self.player.name + ' tried to twinned cast ' + self.spell_name + ' but has not enough sorcery points']
        ifstatements(rules, errors, self.DM).check()
        #If twinned spell is known and sorcery Points there, cast spell twice 
        if self.make_action_check() == True:
            #player should be able to cast, so a True came back. But in the macke_action_check function the bonus_action, action, and/or cast was diabled, so it will be enabled here before casting 
            if cast_level==False:
                cast_level = self.spell_level
            if cast_level == 0:
                self.player.sorcery_points -= 1
            else:
                self.player.sorcery_points -= cast_level
                self.player.spell_slot_counter[cast_level -1] += 1 #add another spell Slots as two will be used in the twin cast
            self.DM.say(self.player.name + ' twinned casts ' + self.spell_name)
            if self.is_concentration_spell and self.is_twin_castable:
                #Must enable these here again, as they are disabled in make_action_check()
                if self.is_bonus_action_spell:
                    self.player.bonus_action = 1
                else:
                    self.player.action = 1
                if self.is_cantrip == False:
                    self.player.cast = 1
                #This kind of spells must handle their twin cast in the cast function
                self.cast(targets, cast_level, twinned=True)
            else:
                for x in targets:
                    #everything will be enabeled in order for the spell do be cast twice
                    if self.is_bonus_action_spell:
                        self.player.bonus_action = 1
                    else:
                        self.player.action = 1
                    if self.is_cantrip == False:
                        self.player.cast = 1
                    self.cast(x, cast_level)

    def quickened_cast(self, targets, cast_level=False):
        rules = [self.player.knows_quickened_spell,
                self.player.sorcery_points >= 2,
                self.player.quickened_spell==0]
        errors = [self.player.name + ' tried to use Quickened Spell without knowing it',
                self.player.name + ' tried to use quickened Spell, but has no Sorcery Points left',
                self.player.name + ' tried to use quickened spell, but has already used it']
        ifstatements(rules, errors, self.player.DM).check()

        self.player.sorcery_points -= 2
        self.player.quickened_spell = 1  #see make_spell_check
        self.DM.say(self.player.name + ' used Quickened Spell')
        if cast_level==False:
            cast_level = self.spell_level
        self.cast(targets, cast_level)

#---------------DMG Scores---------------
#This Scores are returned to the choose_spell_AI function and should resemble about 
#the dmg that the spell makes or an appropriate counter value if the spell does not 
#make direkt dmg, like haste or entangle
#The Function must also return the choosen Targets and Cast Level
#If a Score 0 is returned the spell will not be considered to be cast that way
#The individual sores are in the subclasses

    def hit_propability(self, target):
    #This function evaluetes how propable a hit with a spell attack will be
        SpellToHit = self.player.spell_mod + self.player.proficiency
        AC = target.AC
        prop = (20 - AC + SpellToHit)/20
        return prop

    def save_sucess_propability(self, target):
        SaveMod = target.modifier[self.spell_save_type]
        Advantage = target.check_advantage(self.spell_save_type, notSilent = False)
        #Save Sucess Propability:
        prop = (20 - self.player.spell_dc + SaveMod)/20
        if Advantage < 0:
            prop = prop*prop  #Disadvantage, got to get it twice
        elif Advantage > 0:
            prop = 1 - (1-prop)**2  #would have to miss twice
        return prop

    def dmg_score(self, SpellTargets, dmg, dmg_type, SpellAttack=True, SpellSave=False):
        DMGScore = 0
        for target in SpellTargets:
            target_dmg = dmg
            if SpellSave: #Prop that target makes save
                target_dmg = dmg/2 + (dmg/2)*(1-self.save_sucess_propability(target))
            if SpellAttack:   #it you attack, account for hit propabiltiy
                target_dmg = target_dmg*self.hit_propability(target)#accounts for AC
            #DMG Type, Resistances and stuff
            if dmg_type in target.damage_vulnerability:
                target_dmg = target_dmg*2
            elif dmg_type in target.damage_resistances:
                target_dmg = target_dmg/2
            elif dmg_type in target.damage_immunity:
                target_dmg = 0
            DMGScore += target_dmg #Add this dmg to Score

            #Account for Hex
            if target.is_hexed and self.player.is_hexing:
                for HexToken in self.player.CurrentHexToken.links: #This is your Hex target
                    if HexToken.TM.player == target:
                        DMGScore += 3.5
                        break
        return DMGScore

    def return_0_score(self):
        #this function returns a 0 score, so that spell is not cast
        Score = 0
        SpellTargets = [self.player]
        CastLevel = 0
        return Score, SpellTargets, CastLevel

    def random_score_scale(self):
        Scale = 0.6+0.8*random()
        return Scale

    def choose_smallest_slot(self, MinLevel, MaxLevel):
        #Returns the smallest spellslot that is still available in the range
        #MaxLevel is cast level, so MaxLevel = 4 means Level 4 Slot
        #False, no Spell Slot available
        if MaxLevel > 9: MaxLevel = 9
        if MinLevel < 1: MinLevel = 1
        for i in range(MinLevel-1, MaxLevel):
            if self.player.spell_slot_counter[i]>0:  #i = 0 -> lv1 slot
                return i+1
        return False 

    def choose_highest_slot(self, MinLevel, MaxLevel):
        #Returns the highest spellslot that is still available in the range
        #MinLevel is cast level, so MinLevel = 4 means Level 4 Slot
        #False, no Spell Slot available
        if MaxLevel > 9: MaxLevel = 9
        if MinLevel < 1: MinLevel = 1
        for i in reversed(range(MinLevel-1, MaxLevel)):
            if self.player.spell_slot_counter[i]>0:
                return i+1
        return False 

#Specialized Spell Types
class attack_spell(spell):
    #This Class is a spell that makes one or more single target spell attacks
    def __init__(self, player, dmg_type, number_of_attacks = 0):
        super().__init__(player)
        self.number_of_attacks = number_of_attacks
        self.dmg_type = dmg_type
        self.spell_text = 'spell name' #This will be written as the spell name in print
    
    def cast(self, targets, cast_level=False, twinned=False):
        if type(targets) != list:
            targets = [targets]  #if a list, take first target
        super().cast(targets, cast_level, twinned) #self.cast_level is not set
        #Cast is authorized, so make a spell attack
        tohit = self.player.spell_mod + self.player.proficiency
        dmg = self.spell_dmg()

        if self.player.empowered_spell:
            dmg = dmg*1.21
            self.player.empowered_spell = False #reset empowered spell
            self.DM.say('Empowered: ', end='')

        #Everything is set up and in order
        #Now make the attack/attacks       
        return self.make_spell_attack(targets, dmg, tohit)

    def make_spell_attack(self,targets, dmg, tohit):
        #This function is called in cast function and makes the spell attacks
        #all specifications for this spell are given to the attack function
        #Can attack multiple targts, if one target is passed and num of attacks == 1 this is just one attack
        target_counter = 0
        attack_counter = self.number_of_attacks
        dmg_dealed = 0
        while attack_counter > 0:
            dmg_dealed += self.player.attack(targets[target_counter], is_ranged=self.is_range_spell, other_dmg=dmg, damage_type=self.dmg_type, tohit=tohit)
            attack_counter -= 1
            target_counter += 1
            if target_counter == len(targets):
                target_counter = 0  #if all targets were attacked once, return to first
        return dmg_dealed

    def spell_dmg(self):
        #This function will return the dmg according to Cast Level
        print('No dmg defined for spell: ' + self.spell_name)

class save_spell(spell):
    #This Class is a spell that makes one target make a spell save check
    #If it fails the save, an effect occures
    def __init__(self, player, spell_save_type):
        #spell save type is what check they make
        super().__init__(player)
        self.spell_save_type = spell_save_type
        self.spell_text = 'spell name' #This will be written as the spell name in print

    def cast(self, target, cast_level=False, twinned=False):
        super().cast(target, cast_level, twinned)
        self.make_save(self, target, twinned)

    def make_save(self, target, twinned):
        #Single Target only
        if type(target) == list:
            target = target[0]
        
        target.last_attacker = self.player #target remembers last attacker/spell
        save = target.make_save(self.spell_save_type, DC = self.player.spell_dc) #make the save
        if save < self.player.spell_dc:
            #If failed, then take the individual effect
            self.DM.say(': failed the save')
            self.take_effect(target, twinned)
        else:
            self.DM.say(': made the save')
    
    def take_effect(self, target, twinned):
        #Take effect on a single target
        #This must be implemented in the subclasses
        print('The Save Spell has no effect')
        quit()

class aoe_dmg_spell(spell):
    #This class is a spell that targts multiple targts with a AOE dmg spell
    #On a Save the target gets half dmg
    def __init__(self, player, spell_save_type, dmg_type):
        super().__init__(player)
        self.spell_save_type = spell_save_type #What kind of save
        self.dmg_type = dmg_type
        self.spell_text = 'spell name' #This will be written as the spell name in print

    def cast(self, targets, cast_level=False, twinned=False):
        #Multiple Targts
        if type(targets) != list: targets = [targets]
        super().cast(targets, cast_level, twinned) #self.cast_level now set

        #Damage and empowered Spell
        damage = self.spell_dmg()
        if self.player.empowered_spell:
            damage = damage*1.21
            self.player.empowered_spell = False
            self.DM.say('Empowered: ', end='')

        for target in targets:
            #Every target makes save
            self.make_save_for(target, damage=damage)

    def make_save_for(self, target, damage):
        #This function is called for every target to make the save and apply the dmg
        save = target.make_save(self.spell_save_type,DC = self.player.spell_dc)
        if save >= self.player.spell_dc:
            self.apply_dmg(target, damage=damage/2)
        else: self.apply_dmg(target, damage=damage)

    def apply_dmg(self, target, damage):
        #This finally applies the dmg dealed
        dmg_to_apply = dmg(damage, self.dmg_type)
        target.last_attacker = self.player
        target.changeCHP(dmg_to_apply, self.player, True)

    def spell_dmg(self):
        #This function will return the dmg according to Cast Level
        print('No dmg defined for spell: ' + self.spell_name)

#Specific Spells
#Cantrips
class firebolt(attack_spell):
    def __init__(self, player):
        self.firebolt_dmg = 0
        if player.level < 5:
            self.firebolt_dmg = 5.5
        elif player.level < 11:
            self.firebolt_dmg = 5.5*2
        elif player.level < 17:
            self.firebolt_dmg = 5.5*3
        else:
            self.firebolt_dmg = 5.5*4
        dmg_type = 'fire'
        self.spell_name = 'FireBolt'
        super().__init__(player, dmg_type)
        self.spell_text = 'fire bolt'
        self.spell_level = 0
        self.is_cantrip = True
        self.is_range_spell = True
        self.is_twin_castable = True
    
    def spell_dmg(self):
        return self.firebolt_dmg

class chill_touch(attack_spell):
    def __init__(self, player):
        dmg_type = 'necrotic'
        self.spell_name = 'ChillTouch'

        self.chill_touch_dmg = 0
        #Calculate DMG
        if player.level < 5:
            self.chill_touch_dmg = 4.5
        elif player.level < 11:
            self.chill_touch_dmg = 4.5*2
        elif player.level < 17:
            self.chill_touch_dmg = 4.5*3
        else:
            self.chill_touch_dmg = 4.5*4

        super().__init__(player, dmg_type)
        self.spell_text = 'chill touch'
        self.spell_level = 0
        self.is_cantrip = True
        self.is_range_spell = False
        self.is_twin_castable = True

    def spell_dmg(self):
        return self.chill_touch_dmg
    
    def cast(self, target, cast_level=0, twinned=False):
        #class cast function returns dealed dmg
        dmg_dealed = super().cast(target, cast_level, twinned)

        if dmg_dealed > 0:
            target.chill_touched = True
            self.DM.say(str(target.name) + ' was chill touched')

class eldritch_blast(attack_spell):
    def __init__(self, player):
        self.blast_dmg = 5.5
        dmg_type = 'force'
        self.spell_name = 'EldritchBlast'
        super().__init__(player, dmg_type)

        #Number of attacks at higher level 
        if player.level < 5:
            self.number_of_attacks = 1
        elif player.level < 11:
            self.number_of_attacks = 2
        elif player.level < 17:
            self.number_of_attacks = 3
        else:
            self.number_of_attacks = 4

        self.spell_text = 'eldritch blast'
        self.spell_level = 0
        self.is_cantrip = True
        self.is_range_spell = True
        self.is_twin_castable = False
    
    def spell_dmg(self):
        spell_dmg = self.blast_dmg
        #Aganizing Blast
        if self.player.knows_agonizing_blast:
            spell_dmg += self.player.modifier[5] #Add Cha Mod
        return spell_dmg

    def cast(self, targets, cast_level=False, twinned=False):
        if self.player.knows_agonizing_blast:
            self.DM.say('Agonizing: ', end='')
        super().cast(targets, cast_level, twinned)

#1-Level Spell
class burning_hands(aoe_dmg_spell):
    def __init__(self, player):
        spell_save_type = 1 #Dex
        self.spell_name = 'BurningHands'
        super().__init__(player, spell_save_type, dmg_type='fire')
        self.spell_text = 'burning hands'
        self.spell_level = 1
        self.is_range_spell = True

    def spell_dmg(self):
        #Return the spell dmg
        damage = 7 + 3.5*(self.cast_level)   #upcast dmg 3d6 + 1d6 per level over 2
        return damage

class magic_missile(spell):
    def __init__(self, player):
        self.spell_name = 'MagicMissile'
        super().__init__(player)
        self.spell_text = 'magic missile'
        self.spell_level = 1
        self.is_range_spell = True
    
    def cast(self, targets, cast_level=False, twinned=False):
        damage = 3.5   #1d4 + 1
        if self.player.empowered_spell:
            damage = damage*1.21
            self.player.empowered_spell = False
            self.DM.say('Empowered: ', end='')
        super().cast(targets, cast_level, twinned)
        if type(targets) != list: targets = [targets]
        self.hurl_missile(targets, damage)

    def hurl_missile(self, targets, damage):
        missile_counter = 2 + self.cast_level          #overcast mag. mis. for more darts 
        target_counter = 0
        while missile_counter > 0:    #loop for missile cast
            missile_counter -= 1
            Dmg = dmg(damage, 'force')
            #Check for Hex
            self.player.check_hex(Dmg, targets[target_counter])
            targets[target_counter].last_attacker = self.player    #target remembers last attacker
            targets[target_counter].changeCHP(Dmg, self.player, True)    #target takes damage
            target_counter += 1
            if target_counter == len(targets):    #if all targets are hit once, restart 
                target_counter = 0

class guiding_bolt(attack_spell):
    def __init__(self, player):
        dmg_type = 'radiant'
        self.spell_name = 'GuidingBolt'
        super().__init__(player, dmg_type)
        self.spell_text = 'guifing bolt'
        self.spell_level = 1
        self.is_twin_castable = True
        self.is_range_spell = True

    def cast(self, target, cast_level=False, twinned=False):
        dmg_dealed = super().cast(target, cast_level, twinned)

        #On hit:
        if dmg_dealed > 0:
            LinkToken = GuidingBoltedToken(target.TM) #Target gets guiding bolted token
            GuidingBoltToken(self.TM, [LinkToken]) #Timer Dock Token for player
   
    def spell_dmg(self):
        return 11 + 5.5*self.cast_level #3d10 + 1d10/level > 1

class entangle(save_spell):
    def __init__(self, player):
        spell_save_type = 0 #str
        self.spell_name = 'Entangle'
        super().__init__(player, spell_save_type)
        self.spell_text = 'entangle'
        self.spell_level = 1
        self.is_twin_castable = True
        self.is_concentration_spell = True
        self.is_range_spell = True
    
    def cast(self, targets, cast_level=False, twinned=False):
        #Rewrite cast function to be suited for entangle
        #Entangle takes one target, or two if twinned
        if len(targets) > 2 or len(targets) == 2 and twinned == False: 
            print('Too many entangle targets')
            quit()
        if cast_level == False: cast_level = self.spell_level
        self.autorize_cast(cast_level) #self.cast_level now set
        self.player.DM.say(self.player.name + ' casts ' + self.spell_text)

        self.EntangleTokens = [] #List for entagle Tokens
        for target in targets:
            self.make_save(target, twinned)  #This triggeres the super class make save function, if failed the take_effect function is called
        if len(self.EntangleTokens) != 0:
            ConcentrationToken(self.TM, self.EntangleTokens)
            #player is concentrating on a Entagled Target or targets

    def take_effect(self, target, twinned):
        EntangleToken = EntangledToken(target.TM, subtype='r') #Target gets a entangled token
        self.EntangleTokens.append(EntangleToken) #Append to list

class cure_wounds(spell):
    def __init__(self, player):
        self.spell_name = 'CureWounds'
        super().__init__(player)
        self.spell_text = 'cure wounds'
        self.spell_level = 1
        self.is_twin_castable = True
    
    def cast(self, target, cast_level=False, twinned=False):
        if type(target) == list: target = target[0]
        super().cast(target, cast_level, twinned)
        heal = 4.5*self.cast_level + self.player.spell_mod
        self.DM.say(self.player.name + ' touches ' + target.name + ' with magic:', end='')
        target.changeCHP(dmg(-heal, 'heal'), self.player, False)

class healing_word(spell):
    def __init__(self, player):
        self.spell_name = 'HealingWord'
        super().__init__(player)
        self.spell_text = 'healing word'
        self.spell_level = 1
        self.is_twin_castable = True
        self.is_range_spell = True
        self.is_bonus_action_spell = True
    
    def cast(self, target, cast_level=False, twinned=False):
        if type(target) == list: target = target[0]
        super().cast(target, cast_level, twinned)
        heal = 2.5*self.cast_level + self.player.spell_mod
        if heal < 0: heal = 1
        self.DM.say(self.player.name + ' speaks to ' + target.name, end='')
        target.changeCHP(dmg(-heal, 'heal'), self.player, True)

class hex(spell):
    def __init__(self, player):
        self.spell_name = 'Hex'
        super().__init__(player)
        self.spell_text = 'hex'
        self.spell_level = 1
        self.is_twin_castable = False
        self.is_range_spell = True
        self.is_concentration_spell = True
    
    def cast(self, target, cast_level=False, twinned=False):
        if type(target) == list: target = target[0]
        super().cast(target, cast_level, twinned)
        HexToken = HexedToken(target.TM, subtype='hex') #hex the Tagret
        self.player.CurrentHexToken = HexingToken(self.TM, HexToken) #Concentration on the caster
        #Assign that Token as the Current HEx Token of the Player

    def change_hex(self, target):
        rules = [self.player.can_choose_new_hex,
                self.is_known,
                target.state == 1,
                self.player.bonus_action == 1]
        errors = [self.player.name + ' tried to change a bound hex',
                self.player.name + ' tried to change a hex without knowing it',
                self.player.name + ' tried to change to a not conscious target',
                self.player.name + ' tried to change a hex without having a bonus action']
        ifstatements(rules, errors, self.DM).check()

        self.DM.say(self.player.name + ' changes the hex to ' + target.name)
        self.player.bonus_action = 0 #takes a BA
        self.player.can_choose_new_hex = False
        NewHexToken = HexedToken(target.TM, subtype='hex') #hex the Tagret
        self.player.CurrentHexToken.addLink(NewHexToken) #Add the new Hex Token

class armor_of_agathys(spell):
    def __init__(self, player):
        self.spell_name = 'ArmorOfAgathys'
        super().__init__(player)
        self.spell_text = 'armor of agathys'
        self.spell_level = 1
    
    def cast(self, target, cast_level=False, twinned=False):
        super().cast(target, cast_level, twinned)
        player = self.player
        player.has_armor_of_agathys = True
        TempHP = 5*self.cast_level
        player.agathys_dmg = TempHP
        player.addTHP(TempHP) #add THP to self

class false_life(spell):
    def __init__(self, player):
        self.spell_name = 'FalseLife'
        super().__init__(player)
        self.spell_text = 'false life'
        self.spell_level = 1
    
    def cast(self, target, cast_level=False, twinned=False):
        super().cast(target, cast_level, twinned)
        TempHP = 1.5 + 5*self.cast_level
        self.player.addTHP(TempHP) #Add the THP

class shield(spell):
    def __init__(self, player):
        self.spell_name = 'Shield'
        super().__init__(player)
        self.spell_text = 'shield'
        self.spell_level = 1
        self.is_reaction_spell = True
    
    def cast(self, target=False, cast_level=False, twinned=False):
        super().cast(target, cast_level, twinned)
        self.player.AC += 5

class inflict_wounds(attack_spell):
    def __init__(self, player):
        dmg_type = 'necrotic'
        self.spell_name = 'InflictWounds'
        super().__init__(player, dmg_type)
        self.spell_text = 'inflict wounds'
        self.spell_level = 1
        self.is_twin_castable = True
    
    def spell_dmg(self):
        return 11 + 5.5*self.cast_level #3d10 + 1d10/level > 1

#2-Level Spell

class scorching_ray(attack_spell):
    def __init__(self, player):
        dmg_type = 'fire'
        self.spell_name = 'ScorchingRay'
        super().__init__(player, dmg_type)
        self.spell_text = 'scorching ray'
        self.spell_level = 2
        self.is_range_spell = True
    
    def spell_dmg(self):
        return 7 #2d6 dmg per ray

    def cast(self, targets, cast_level=False, twinned=False):
        if cast_level == False: cast_level = self.spell_level
        self.number_of_attacks = 1 + cast_level
        #Set the number of attacks, then let the super cast function handle the rest
        super().cast(targets, cast_level, twinned)

class aganazzars_sorcher(aoe_dmg_spell):
    def __init__(self, player):
        spell_save_type = 1 #Dex
        self.spell_name = 'AganazzarsSorcher'
        super().__init__(player, spell_save_type, dmg_type='fire')
        self.spell_text = 'aganazzars scorcher'
        self.spell_level = 2
        self.is_range_spell = True

    def spell_dmg(self):
        #Return the spell dmg
        damage = 13.5 + 4.5*(self.cast_level-2)   #upcast dmg 3d6 + 1d6 per level over 2
        return damage

class shatter(aoe_dmg_spell):
    def __init__(self, player):
        spell_save_type = 2 #Con
        self.spell_name = 'Shatter'
        super().__init__(player, spell_save_type, dmg_type='thunder')
        self.spell_text = 'shatter'
        self.spell_level = 2
        self.is_range_spell = True

    def spell_dmg(self):
        #Return the spell dmg
        damage = 13.5 + 4.5*(self.cast_level-2)   #upcast dmg 3d6 + 1d6 per level over 2
        return damage

class spiritual_weapon(spell):
    def __init__(self, player):
        self.spell_name = 'SpiritualWeapon'
        super().__init__(player)
        self.spell_text = 'spiritual weapon'
        self.spell_level = 1
    
    def cast(self, target, cast_level=False, twinned=False):
        super().cast(target, cast_level, twinned)
        #remember, if use cast level, use self.cast_level not cast_level
        player = self.player
        player.has_spiritual_weapon = True
        player.SpiritualWeaponDmg = player.spell_mod + 4.5*(self.cast_level -1) 
        player.SpiritualWeaponCounter = 0 #10 Rounds of Weapon

        #If a player cast this spell for the first time, the choice will be aded to the AI
        #The Score function will still check if the player is allowed to use it
        
        player.AI.Choices.append(player.AI.spiritualWeaponChoice)

        #Attack Once as BA
        if player.bonus_action == 1:
            self.spiritual_weapon_attack(target)

    def use_spiritual_weapon(self, target):
        player = self.player
        rules = [player.has_spiritual_weapon,
                player.bonus_action == 1]
        errors = [player.name + ' tried using the Spiritual Weapon without having one',
                player.name + ' tried using the Spiritual Weapon without having a bonus action']
        ifstatements(rules, errors, self.DM).check()

        self.spiritual_weapon_attack(target)

    def spiritual_weapon_attack(self, target):
        if type(target) == list:
            target = target[0]
        player = self.player
        WeaponTohit = player.spell_mod + player.proficiency #ToHit of weapon
        WeaponDmg = player.SpiritualWeaponDmg #Set by the Spell 
        self.DM.say('Spiritual Weapon of ' + player.name + ' attacks: ')
        #Make a weapon Attack against first target
        self.player.attack(target, is_ranged=False, other_dmg=WeaponDmg, damage_type='force', tohit=WeaponTohit)
        self.player.bonus_action = 0 #It uses the BA to attack

#3-Level Spell
class fireball(aoe_dmg_spell):
    def __init__(self, player):
        spell_save_type = 1 #Dex
        self.spell_name = 'Fireball'
        super().__init__(player, spell_save_type, dmg_type='fire')
        self.spell_text = 'fireball'
        self.spell_level = 3
        self.is_range_spell = True

    def spell_dmg(self):
        #Return the spell dmg
        damage = 28 + 3.5*(self.cast_level-3)   #upcast dmg 3d6 + 1d6 per level over 2
        return damage

class lightningBolt(aoe_dmg_spell):
    def __init__(self, player):
        spell_save_type = 1 #Dex
        self.spell_name = 'LightningBolt'
        super().__init__(player, spell_save_type, dmg_type='lightning')
        self.spell_text = 'lightning bolt'
        self.spell_level = 3
        self.is_range_spell = True

    def spell_dmg(self):
        #Return the spell dmg
        damage = 28 + 3.5*(self.cast_level-3)   #upcast dmg 3d6 + 1d6 per level over 2
        return damage

class haste(spell):
    def __init__(self, player):
        self.spell_name = 'Haste'
        super().__init__(player)
        self.spell_text = 'haste'
        self.spell_level = 3
        self.is_twin_castable = True
        self.is_concentration_spell = True
        self.is_range_spell = True
    
    def cast(self, targets, cast_level=False, twinned=False):
        if len(targets) > 2 or len(targets) == 2 and twinned == False: 
            print('Too many entangle targets')
            quit()
        super().cast(targets, cast_level, twinned)
        HasteTokens = []
        for target in targets:
            HasteToken = HastedToken(target.TM, subtype='h')
            HasteTokens.append(HasteToken)
            self.DM.say(self.player.name + ' gives haste to ' + target.name)
        ConcentrationToken(self.TM, HasteTokens)
        #Player is now concentrated on 1-2 Haste Tokens

class conjure_animals(spell):
    def __init__(self, player):
        self.spell_name = 'ConjureAnimals'
        super().__init__(player)
        self.spell_text = 'conjure animals'
        self.spell_level = 3
        self.is_concentration_spell = True

    def cast(self, fight, cast_level=False, twinned=False):
        #Im am using a trick here, ususally only a target is passed, but this spell needs the fight
        #As a solution the score function of this spell passes the fight as 'targtes' 
        #The cunjured Animals are initiated as fully functunal entity objects
        #The Stats are loaded from the Archive
        #If they reach 0 CHP they will die and not participate in the fight anymore
        #The do_the_fighting function will then pic them out and delete them from the fight list
        super().cast(fight, cast_level, twinned)

        Number, AnimalName = self.choose_animal()
        player = self.player
        #Initiate a new entity for the Animals and add them to the fight
        conjuredAnimals = []
        for i in range(0,Number):
            animal = entity(AnimalName, player.team, player.DM, archive=True)
            animal.name = 'Conjured ' + AnimalName + str(i+1)
            self.DM.say(animal.name + ' appears')
            animal.summoner = player
            fight.append(animal)

            conjuredAnimals.append(SummenedToken(animal.TM, 'ca')) #add a SummonedToken to the animal
        #Add a Summoner Token to the Player
        SummonerToken(self.TM, conjuredAnimals)



    def choose_animal(self):
        level = 10 #will be set to Beast level for test
        while level > 2:
            Index = int(random()*len(self.player.BeastForms))
            AnimalName = self.player.BeastForms[Index]['Name'] #Random Animal
            level = self.player.BeastForms[Index]['Level'] #Choose a Animal of level 2 or less

        Number = int(2/level)     #8 from CR 1/4, 4 from CR 1/2 ...
        
        if self.cast_level < 5:
            Number = Number
        elif self.cast_level < 7:
            Number = Number*2
        elif self.cast_level < 9: 
            Number = Number*3
        else: 
            Number = Number*4
        
        return Number, AnimalName

#4-Level Spell

class blight(aoe_dmg_spell):
    #has aoe as super class, will be modified for single target
    def __init__(self, player):
        spell_save_type = 1 #Dex
        self.spell_name = 'Blight'
        super().__init__(player, spell_save_type, dmg_type='necrotic')
        self.spell_text = 'blight'
        self.spell_level = 4
        self.is_range_spell = True
        self.is_twin_castable = True

    def cast(self, target, cast_level=False, twinned=False):
        if target == list: target = target[0] #mod for single cast
        super().cast(target, cast_level, twinned)

    def make_save_for(self, target, damage):
        #This function is called for every target to make the save and apply the dmg
        #It is only called once, for one target

        #calculate damage manually to account for plants
        damage = 18 + 4.5*(self.cast_level)   #upcast dmg 3d6 + 1d6 per level over 2
        extraAdvantage = 0
        if target.type == 'plant':
            extraAdvantage = -1 #disadvantage for plants
            damage = 32 + 8*self.cast_level #max dmg
            self.DM.say('is plant: ', end ='')
        save = target.make_save(self.spell_save_type,DC = self.player.spell_dc, extraAdvantage=extraAdvantage)

        if target.type == 'undead' or target.type == 'construct':
            self.DM.say('\nIs undead or construct and immune', end='')
            self.apply_dmg(target, damage=0) #no effect on this types        
        elif save >= self.player.spell_dc:
            self.apply_dmg(target, damage=damage/2)        
        else: self.apply_dmg(target, damage=damage)
    
    def spell_dmg(self):
        return 0 #will not be used anyway for blight