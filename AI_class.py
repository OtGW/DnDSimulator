from random import random, shuffle
import numpy as np
import Choice_class as ch
from functools import partial

if __name__ == '__main__':
    from Entity_class import entity
              
class AI:
    def __init__(self, player):
    #this class is initialized in the Entity class to controll all the moves and decisions
        self.player = player
        if self.player.DM.AI_blank: #this is only a dirty trick so that VScode shows me the attributes of player and MUST be deactived
            self.player = entity('test', 0, 0)

        #this is later filled in do_your_turn()
        self.allies = [] #only Allies left alive
        self.dying_allies = []

        #---------TEST---------
        self.Choices = [
            ch.do_attack(player),
            ch.do_offhand_attack(player),
            ch.do_spellcasting(player),
            ch.do_monster_ability(player),
            ch.do_heal(player)
        ]
        if self.player.knows_inspiration:
            self.Choices.append(ch.do_inspire(player))
        if self.player.knows_action_surge:
            self.Choices.append(ch.use_action_surge(player))
        if self.player.knows_turn_undead:
            self.Choices.append(ch.do_turn_undead(player))
        if self.player.knows_wild_shape:
            self.Choices.append(ch.go_wildshape(player))

    def do_your_turn(self,fight):
        player = self.player
        self.allies = [x for x in fight if x.team == player.team and x.state != -1]       #which allies
        self.dying_allies = [i for i in self.allies if i.state == 0]     #who is dying

        #stand up if prone
        if player.prone == 1 and player.restrained == 0:
            player.stand_up()

        #Aura of Protection (Passiv) resets at the start of do your turn by the player emitting the aura
        #It is handeled via DM relations
        #First resolve all old relations
        OldAuraRelations = [x for x in player.DM.relations if x.type == 'AuraOfProtection' and x.initiator == player]
        for x in OldAuraRelations: player.DM.resolve(x)
        #Choosing new Aura targets:
        if player.knows_aura_of_protection: player.use_aura_of_protection(self.allies)

        #Choose new Hex
        if player.can_choose_new_hex: self.choose_new_hex(fight)
        
        #Use Second Wind
        if player.knows_second_wind and player.has_used_second_wind == False:
            if player.bonus_action == 1:
                if player.CHP/player.HP < 0.3: player.use_second_wind()

        #Interseption
        if player.knows_interseption:
            self.allies[int(random()*len(self.allies))].interseption_amount = 5.5 + player.proficiency

        #------------Not in WildShape
        if player.wild_shape_HP == 0:
        #--------Evaluate Choices
            while (player.action == 1 or player.bonus_action == 1) and player.state == 1:
                ChoiceScores = [choice.score(fight) for choice in self.Choices] #get Scores
                ActionToDo = self.Choices[np.argmax(ChoiceScores)]
                if np.max(ChoiceScores) > 0:
                    ActionToDo.execute(fight) #Do the best Choice
                #First Round Action and Attacks
                #Secound Round Bonus Action
                #Check is still smth to do, else return
                if sum(ChoiceScores) == 0:
                    rules = [player.bonus_action == 1 and player.action == 1,
                        player.attack_counter > 0,
                        len([x for x in fight if x.team != player.team and x.state == 1]) == 0]
                    if all(rules):
                        player.DM.say(player.name + ' count not decide what to do!')
                        quit()
                    return

        #------------Still in Wild Shape
        else: self.smart_in_wildshape(fight)

#-----------Smart Actions
    def smart_in_wildshape(self, fight):
        player = self.player
        #This function is called in do_your_turn if the player is still in wild shape
        if self.dying_allies != []:
        #is someone dying
            dying_allies_deathcounter = np.array([i.death_counter for i in self.dying_allies])
            if np.max(dying_allies_deathcounter) > 1:
                if player.SpellBook['CureWounds'].is_known and sum(player.spell_slot_counter) > 0 and player.bonus_action == 1:
                    player.wild_reshape()
                    target = self.dying_allies[np.argmax(dying_allies_deathcounter)]
                    for i in range(0,9):
                        if player.spell_slot_counter[i]>0:
                            player.SpellBook['CureWounds'].cast(target, cast_level=i+1)
                            break  
                    self.do_your_turn(fight) #this then starts the healing part again

        #Heal in combat wild shape
        self.try_wild_shape_heal()
        if player.action == 1:
            ch.do_attack(player).execute(fight)
    
    def try_wild_shape_heal(self):
        player = self.player
        if player.knows_combat_wild_shape and player.bonus_action == 1:
            #if wild shape is low < 1/4
            if 0 < player.wild_shape_HP < player.wild_shape_HP/4:
                #Still have spell slots?
                for i in range(0,7):
                    if player.spell_slot_counter[6-i] > 0: #try all spell slots, starting at 6
                        player.use_combat_wild_shape_heal(spell_level=6-i+1) #spelllevel is 1+i

#---------Reaction
    def do_opportunity_attack(self,target):
        #this function is called when the player can do an attack of opportunity
        if target.knows_cunning_action and target.bonus_action == 1:
            target.use_disengage() #use cunning action to disengage
            return
        else:
            if self.player.has_range_attack: is_ranged = True
            else: is_ranged = False
            self.player.attack(target, is_ranged, is_opportunity_attack = True)

    def want_to_cast_shield(self, attacker, damage):
        #This function is called in the attack function as a reaction, if Shild spell is known
        if self.player.CHP < damage.abs_amount():
            for i in range(9):
                if self.player.spell_slot_counter[i] > 0:
                    self.player.SpellBook['Shield'].cast(i + 1)   #spell level is i + 1
                    break

#---------Support
    def area_of_effect_chooser(self, fight, area):   #area in square feet
    #The chooser takes all enemies and chooses amoung those to hit with the area of effect
    #every target can only be hit once, regardless if it is alive or dead 
    #how many targets wil be hit depends on the area and the density in that area from the Battlefield.txt
        enemies = [x for x in fight if x.team != self.player.team and x.state != -1]
        DensityFaktor = 2
        if self.player.DM.density == 0: DensityFaktor = 1
        elif self.player.DM.density == 2: DensityFaktor = 3
        target_pool = (area/190)**(1/3)*DensityFaktor - 0.7   #how many enemies should be in that area
        #0 is wide space
        #1 is normal
        #2 is crowded


        if target_pool < 1: target_pool = 1     #at least one will be hit 
        if target_pool < 2 and area > 100 and len(enemies) > 3: 
            if random() > 0.6 - area/500:
                target_pool = 2 #usually easy to hit 2
        elif target_pool == 2 and area > 300 and len(enemies) > 6: target_pool = 3

        if target_pool > len(enemies)*0.8 and len(enemies) > 2: #will rarely hit all
            target_pool = target_pool*0.7
        
        target_pool = target_pool*(random()*0.64 + 0.63) + 0.5 #a little random power 
        target_pool += len(enemies)/12*(0.15 + random()*0.55)

        target_pool = int(target_pool)
        shuffle(enemies)
        if len(enemies) < target_pool:
            targets = enemies
        else:
            targets = enemies[0:target_pool]

        #This returns: 
        # 3 ebemies
        #    115: [1000.    0.    0.    0.    0.    0.    0.    0.    0.    0.]
        #    300: [366. 634.   0.   0.   0.   0.   0.   0.   0.   0.]
        #    450: [145. 767.  88.   0.   0.   0.   0.   0.   0.   0.]
        #    800: [254. 746.   0.   0.   0.   0.   0.   0.   0.   0.]
        #    1250: [ 40. 717. 243.   0.   0.   0.   0.   0.   0.   0.]
        #    4000: [  0. 133. 867.   0.   0.   0.   0.   0.   0.   0.]
        # 4 enemies
        #    115: [521. 393.  86.   0.   0.   0.   0.   0.   0.   0.]
        #    300: [161. 719. 120.   0.   0.   0.   0.   0.   0.   0.]
        #    450: [ 83. 769. 148.   0.   0.   0.   0.   0.   0.   0.]
        #    800: [  0. 463. 537.   0.   0.   0.   0.   0.   0.   0.]
        #    1250: [  0. 213. 512. 275.   0.   0.   0.   0.   0.   0.]
        #    4000: [  0. 125. 472. 403.   0.   0.   0.   0.   0.   0.]


        return targets

    def player_attack_score(self, fight, is_offhand=False):
        #This function return a damage equal value, that should represent the dmg that could be expected form this player if it just attacks
        player = self.player
        Score = 0
        if is_offhand:
            dmg = player.offhand_dmg
            attacks = 1
        else:
            dmg = player.dmg
            attacks = player.attacks

        if is_offhand == False:
            if (player.knows_rage and player.bonus_action == 1) or player.raged == 1:
                dmg += player.rage_dmg
            if player.knows_frenzy:
                attacks += 1
            if player.is_hasted():
                attacks += 1

        if player.knows_reckless_attack:
            dmg = dmg*1.2 #improved chance to hit
        if player.is_entangled():
            dmg = dmg*0.8
        if player.is_hexing():
            dmg += 3.5

        #dmg score is about dmg times the attacks
        #This represents vs a test AC
        TestACs = [x.AC for x in fight if x.team != player.team and x.state != -1]
        if len(TestACs) > 0:
            TestAC = np.mean(TestACs)
        else: TestAC = 16
        Score = dmg*(20 - TestAC + player.tohit)/20*attacks

        #Only on one Attack 
        if player.sneak_attack_counter == 1:
            Score += player.sneak_attack_dmg
        if player.wailsfromthegrave_counter > 0:
            Score += player.sneak_attack_dmg/2
        if player.knows_smite:
            for i in range(0,5):
                if player.spell_slot_counter[4-i] > 0:
                    Score += (4-i)*4.5  #Smite Dmg once

        #Other Stuff
        if player.dash_target != False: #Do you have a dash target?
            if player.dash_target.state == 1: Score*1.5 #Encourage a Dash target attack
        if player.has_range_attack == False:
            Score = Score*np.sqrt(player.AC/(13 + player.level/3.5)) #Encourage player with high AC
        return Score

    def choose_att_target(self, fight, AttackIsRanged = False, other_dmg = False, other_dmg_type = False):
        player = self.player
        if other_dmg == False:
            dmg = player.dmg
        else:
            dmg = other_dmg
        if other_dmg_type == False:
            dmg_type = player.damage_type
        else:
            dmg_type = other_dmg_type
        #function returns False if no target in reach
        #this function takes all targets that are possible in reach and choosed which one is best to attack
        #the AttackIsRanged is to manually tell the function that the Attack is ranged, even if the player might not have ranged attacks, for Spells for example
        EnemiesInReach = player.enemies_reachable_sort(fight, AttackIsRanged)

        if player.dash_target != False:
            if player.dash_target.state == 1:
                #If the Dash Target from last turn is still alive, attack
                return player.dash_target

        if len(EnemiesInReach) == 0:
            player.DM.say('There are no Enemies in reach for ' + player.name + ' to attack')
            player.move_position() #if no target in range, move a line forward
            player.attack_counter = 0
            return False  #return, there is no target
        else:
            target_list = EnemiesInReach
            #This function is the intelligence behind choosing the best target to hit from a List of given Targets. It chooses reguarding lowest Enemy and AC and so on
            ThreatScore = np.zeros(len(target_list))
            for i in range(0, len(target_list)):
                ThreatScore[i] = self.target_attack_score(fight, target_list[i], dmg_type, dmg)
            return target_list[np.argmax(ThreatScore)]

    def target_attack_score(self, fight, target, dmg_type, dmg):
        player = self.player
        Score = 0
        RandomWeight = 2 #random factor between 1 and the RandomWeight
        TargetDPS = target.dps()
        PlayerDPS = player.dps()

        #Immunity
        if dmg_type in target.damage_immunity:
            return 0      #makes no sense to attack an immune target
        #Dmg done by the creature
        Score += TargetDPS*(random()*RandomWeight + 1) #Damage done per round so far
        #How Low the Enemy is
        Score += TargetDPS*(target.HP - target.CHP)/target.HP*(random()*RandomWeight + 1)
        #Heal given
        Score += target.heal_given/player.DM.rounds_number*(random()*RandomWeight + 1)

        #Target is unconscious or can be One Shot
        if target.state == 0:
            Score += TargetDPS*2*(random()*RandomWeight + 1)
        elif target.CHP <= dmg: #kill is good, oneshot is better
            Score += TargetDPS*4*(random()*RandomWeight + 1)
        elif dmg > target.HP*2: #Can Instakill
            Score += TargetDPS*10*(random()*RandomWeight + 1)

        #Hit low ACs
        if (target.AC - player.tohit)/20 < 0.2:
            Score += TargetDPS*(random()*RandomWeight + 1)
        elif (target.AC - player.tohit)/20 < 0.35:
            Score += TargetDPS/2*(random()*RandomWeight + 1) #Good to hit 
        #Dont Attack high AC
        if (target.AC - player.tohit)/20 > 0.8: #90% no hit prop
            Score -= TargetDPS*(random()*RandomWeight + 1)

        #Attack player with your Vulnerability as dmg
        if target.last_used_DMG_Type in player.damage_vulnerability:
            Score += TargetDPS*(random()*RandomWeight + 1)
        if dmg_type in target.damage_vulnerability:
            Score += TargetDPS*(random()*RandomWeight + 1)
        elif dmg_type in target.damage_resistances:
            Score -= TargetDPS*2*(random()*RandomWeight + 1)


        #Spells
        if player.is_entangled():
            for x in player.DM.relations:
                if x.type == 'Entangle' and x.target == player and x.initiator == target:
                    Score += PlayerDPS*2*(random()*RandomWeight + 1) #This player is entangling you 
        if player.is_hexing():
            for x in player.DM.relations:
                if x.type == 'Hex' and x.target == target and x.initiator == player:
                    Score += (TargetDPS + 3.5)*(random()*RandomWeight + 1) #Youre hexing this player
        if target.is_concentrating: Score += TargetDPS/3*(random()*RandomWeight + 1)
        if target.has_animals_conjured: Score += TargetDPS/2*(random()*RandomWeight + 1)
        if target.has_armor_of_agathys: Score -= PlayerDPS/3*(random()*RandomWeight + 1)
        if target.restrained or target.prone or target.blinded:
            Score += TargetDPS/4*(random()*RandomWeight + 1)

        #Wild shape, it is less useful to attack wildshape forms
        if target.wild_shape_HP > 0 and target.knows_combat_wild_shape == False:
            Score = Score*0.8*(random()*RandomWeight + 1)
        if target.wild_shape_HP <= dmg: 
            Score = Score*1.4*(random()*RandomWeight + 1)

        #Movement (this section takes a lot of time to run, check it)
        NeedDash = player.need_dash(target, fight)
        if NeedDash == 1 and player.knows_cunning_action == False:
            Score -= PlayerDPS/1.3*(random()*RandomWeight + 1)
            #Player cant attack this turn if dashed
        elif NeedDash == 1 and player.knows_cunning_action:
            Score -= dmg/2*(random()*RandomWeight + 1)
        elif NeedDash == 1 and player.knows_eagle_totem:
            Score -= dmg/2*(random()*RandomWeight + 1)
            #With cunning action/eagle totem less of a Problem
        if player.will_provoke_Attack(target, fight):
            if player.knows_eagle_totem:
                Score -= PlayerDPS/6*(random()*RandomWeight + 1)
            elif player.CHP > player.HP/3: 
                Score -= PlayerDPS/4*(random()*RandomWeight + 1)
            else: 
                Score -= PlayerDPS/2*(random()*RandomWeight + 1)

        #Line Score, Frontliner will go for front and mid mainly
        if player.position == 0: #front
            if target.position == 0: Score = Score*1.2*(random()*RandomWeight + 1)
            elif target.position == 1: Score = Score*1.1*(random()*RandomWeight + 1)
        elif player.position == 1: #Mid
            if target.position == 0: Score = Score*1.3*(random()*RandomWeight + 1)
            elif target.position == 1: Score = Score*1.2*(random()*RandomWeight + 1)
            elif target.position == 2: Score = Score*1.1*(random()*RandomWeight + 1)
            elif target.position == 3: Score = Score*1.1*(random()*RandomWeight + 1)
        elif player.position == 2: #Back
            if target.position == 2: Score = Score*1.2*(random()*RandomWeight + 1)
            elif target.position == 3: Score = Score*1.3*(random()*RandomWeight + 1)
        elif player.position == 3: #Airborn
            if target.position == 2: Score = Score*1.2*(random()*RandomWeight + 1)
        
        if target.is_a_turned_undead:
            Score = Score/4 #almost no threat at the moment
        return Score

    def spell_cast_check(self, spell):
        player = self.player
        #This function checks if a given Spell is castable for the player by any means, even with quickened Spell
        #False - not castable
        #1 - castable
        #2 - only Castable via QuickenedSpell
        if spell.is_known == False:
            return False
        #Check if Player has spellslots
        if spell.spell_level > 0:
            good_slots = sum([1 for i in range(spell.spell_level - 1,9) if player.spell_slot_counter[i] > 0])
            if good_slots == 0:
                return False
        
        if player.wild_shape_HP > 0:
            return False
        elif spell.is_concentration_spell and player.is_concentrating:
            return False
        elif spell.is_reaction_spell:
            return False   #reaction Spell in own turn makes no sense
        elif spell.is_cantrip == False and player.cast == 0:
            return False


        #Action Check
        if spell.is_bonus_action_spell and player.bonus_action == 1:
            if spell.is_cantrip:
                return 1         #have BA, is cantrip -> cast 
            elif player.cast == 1:
                return 1        #have BA, is spell, have caste left? -> cast
            else:
                return False    #cant cast, have already casted
        elif spell.is_bonus_action_spell == False:
            if player.action == 1:
                if spell.is_cantrip:
                    return 1 #have action and is cantrip? -> cast
                elif player.cast == 1:
                    return 1 #have action and cast left? -> cast
                else:
                    return False
            elif player.bonus_action == 1 and player.knows_quickened_spell and player.sorcery_points >= 2:
                if spell.is_cantrip:
                    return 2  #Cast only with Quickened Spell
                elif player.cast ==1:
                    return 2  #have cast left?
                else:
                    return False
            else:
                return False
        else:
            return False

    def choose_quickened_cast(self):
        #This function is called once per trun to determine if player wants to use quickned cast this round
        player = self.player
        QuickScore = 100
        QuickScore = QuickScore*(1.5 - 0.5*(player.CHP/player.HP)) #encourage quickend cast if youre low, if CHP -> 0, Score -> 150
        if player.cast == 1: QuickScore = QuickScore*1.4    #encourage if you havend cast yet
        if player.sorcery_points < player.sorcery_points_base/2: QuickScore = QuickScore*0.9 #disencourage for low SP
        elif player.sorcery_points < player.sorcery_points_base/3: QuickScore = QuickScore*0.8
        elif player.sorcery_points < player.sorcery_points_base/5: QuickScore = QuickScore*0.7
        if player.is_entangled(): QuickScore = QuickScore*1.1  #Do something against the entangle
        #Random Power for quickened Spell
        QuickScore = QuickScore*(0.65 + random()*0.7) #+/- 35%
        if QuickScore > 100:
            return True
        else:
            return False

    def choose_spell(self, fight):
        #This function chooses a spell for the spell choice
        #If this function return False, spellcasting is not an option for this choice
        player = self.player
        SpellChoice = False

        #Check the absolute Basics
        if player.action == 0 and player.bonus_action == 0:
            return False, 0
        if player.raged == 1:
            return False, 0   #cant cast while raging

        Choices = []

        #Check Spells
        for spellname in player.SpellNames:
            Checkvalue = self.spell_cast_check(player.SpellBook[spellname])
            if Checkvalue == 1:#check is spell is castable
                Choices.append(player.SpellBook[spellname].cast)
            if Checkvalue == 1 and player.SpellBook[spellname].is_twin_castable and player.knows_twinned_spell and player.sorcery_points > player.SpellBook[spellname].spell_level and player.sorcery_points > 1:
                Choices.append(player.SpellBook[spellname].twin_cast)
            elif Checkvalue == 2: #Spell is only castable via quickened spell
                Choices.append(player.SpellBook[spellname].quickened_cast)

        #This function determines if the player wants to cast a quickened spell this round
        if player.knows_quickened_spell:
            cast_quickened_this_round = self.choose_quickened_cast()
        else:
            cast_quickened_this_round = False

        ChoiceScores = [0 for i in Choices]
        if len(Choices) == 0:
            return False, 0  #if no spell is castable return False
        TargetList = [[player] for i in Choices] #will be filled with targets
        LevelList = [0 for i in Choices]#at what Level the Spell is casted
        for i in range(0, len(Choices)):
            Choice = Choices[i]
            Score = 0

        #In the following all Options will get a score, that roughly resemlbes their dmg or equal dmg value
        #This Score is assigned by a function of the spellcasting class 
        #This function also evalues if it is good to use a quickened or twin cast
        #The evaluation of quickened Cast is currently not handled by these functions
            for spell in player.SpellNames:
                if Choice == player.SpellBook[spell].cast:
                    Score, SpellTargets, CastLevel = player.SpellBook[spell].score(fight)
                elif Choice == player.SpellBook[spell].quickened_cast:
                    if cast_quickened_this_round == True:
                        Score, SpellTargets, CastLevel = player.SpellBook[spell].score(fight)
                    else:
                        #Basically dont cast quickened this round
                        Score = 0
                        SpellTargets = [player]
                        CastLevel = 0
                elif Choice == player.SpellBook[spell].twin_cast:
                    Score, SpellTargets, CastLevel = player.SpellBook[spell].score(fight, twinned_cast=True)

            ChoiceScores[i] = Score
            TargetList[i] = SpellTargets
            LevelList[i] = CastLevel
        #Now find best value and cast that
        ChoiceIndex = np.argmax(ChoiceScores)

        #Before returning the Value check if it is even sensable to cast instaed of doing something else
        #This part gives a Value of the possible alternatives and assignes a dmg equal value to compare with
        #This is the Score that will be compared for the action Spell, so assume an action is left
        if player.action == 1:
            #If the player has still its action, compete with this alternative score
            if np.max(ChoiceScores) > player.dmg:
                SpellChoice = partial(Choices[ChoiceIndex],TargetList[ChoiceIndex],LevelList[ChoiceIndex])
                return SpellChoice, ChoiceScores[ChoiceIndex]
            else:
                return False, 0 #If you have action and cant beat this Score, dont cast spell
        elif player.bonus_action == 1:
            if np.max(ChoiceScores) > player.dmg/5 + 1:    #just a small threshold
                    SpellChoice = partial(Choices[ChoiceIndex],TargetList[ChoiceIndex],LevelList[ChoiceIndex])
                    return SpellChoice, ChoiceScores[ChoiceIndex]
            else:
                return False, 0
        else: return False, 0

    def choose_heal_target(self, fight):
        #This function is called if the player has heal
        #It returns the best Target for a heal and gives the Heal a Score
        #If False is returned, Heal will not be added as a Choice for this turn
        player = self.player
        if self.dying_allies != []:      #someone is dying
            DyingScore = []
            for ally in self.dying_allies:
                Score = ally.dps()*ally.death_counter #High Score for a high death_counter
                Score += ally.value()
                Score = Score*0.7*(0.8+random()*0.4) #little random power
                #The Score will be returned as a Score for the Choices in do_your_turn too
                DyingScore.append(Score)
            MaxIndex = np.argmax(DyingScore)
            Target = self.dying_allies[MaxIndex]
            return Target, DyingScore[MaxIndex]
        #No One is currently dying
        else:
            TeamHP = sum([x.HP for x in self.allies])
            TeamCHP = sum([x.CHP for x in self.allies])
            if TeamCHP/TeamHP < 0.7:
                HealScores = []
                for ally in self.allies:
                    Score = ally.value()*2/3 #Player is not dead, might still do another round
                    Score = Score*(1 - ally.CHP/ally.HP) #Score Scales with CHP left
                    Score = Score*(0.8+random()*0.4)
                    if ally.CHP/ally.HP > 0.6:
                        Score = 0
                    HealScores.append(Score)
                MaxIndex = np.argmax(HealScores)
                if HealScores[MaxIndex] > player.value()/3: #Minimum Boundry for reasonable heal
                    return self.allies[MaxIndex], HealScores[MaxIndex]
                else:
                    return False, 0
            else:
                return False, 0

    def choose_heal_spellslot(self, MinLevel = 1):
        player = self.player
        spells = player.SpellBook['HealingWord']
        #It has no meaning which spell is used, I only want to use the choose lowest/highest spell function
        SpellPower = sum([player.spell_slot_counter[i]*np.sqrt((i + 1)) for i in range(0,9)])
        MaxSlot = 0 # Which is the max spell slot left
        for i in reversed(range(0,9)):
            if player.spell_slot_counter[i] > 0:
                MaxSlot = i + 1
                break

        TestLevel = int(SpellPower/5 + 1.5)
        if TestLevel == MaxSlot:
            #Never use best slot to heal
            TestLevel -= 1
        
        #Use the TestLevel Slot or the next best lower then it
        LowLevel = spells.choose_highest_slot(1,TestLevel)
        if LowLevel != False:
            return LowLevel
        #if no low level left, try higher
        HighLevel = spells.choose_smallest_slot(TestLevel+1,9)
        if HighLevel != False:
            return HighLevel
        return False

    def choose_new_hex(self, fight):
        HexChoices = [x for x in fight if x.team != self.player.team and x.state == 1]
        HexTarget = self.choose_att_target(HexChoices, AttackIsRanged=True, other_dmg=3.5)
        if HexTarget != False:
            self.player.SpellBook['Hex'].change_hex(HexTarget)