from Entity_class import *
from Dm_class import *
from Dmg_class import *
from Token_class import *
import numpy

def reset(fight):
    for x in fight:
        x.long_rest()

def ConcentrationTest1(Character, Enemy):
    Character.SpellBook['Haste'].is_known = True
    Character.spell_slot_counter[2] = 1
    Character.SpellBook['Haste'].cast([Character])
    if Character.is_concentrating == False: 
        print('Not Concentrated after cast')
        quit()
    else:
        Character.CHP = 200
        Character.changeCHP(dmg(100, 'true'), Enemy, was_ranged = False)
        if Character.is_concentrating == True:
            print('Still concentrated after break Con')
            quit()
        else:
            Character.long_rest()
            print('Concentration Test 1')
            return True

def ConcentrationTestEntangle(Character, Enemy):
    Character.SpellBook['Entangle'].is_known = True
    Character.spell_slot_counter[0] = 1
    Character.spell_dc = 100
    Character.SpellBook['Entangle'].cast([Enemy])
    if Character.is_concentrating == False: 
        print('Not Concentrated after cast')
        quit()
    else:
        Enemy.TM.resolveAll()
        if Character.is_concentrating == True:
            print('Still concentrated after break Con')
            quit()
        else:
            print('Concentration Test Entangle')
            return True

def HasteRoundTest(Character):
    Character.SpellBook['Haste'].is_known = True
    Character.spell_slot_counter[2] = 1
    Character.SpellBook['Haste'].cast([Character])
    if Character.is_concentrating == False: 
        print('Not Concentrated after cast')
        quit()
    else:
        for i in range(0,10):
            Character.end_of_turn()
        if Character.is_concentrating:
            print('Still concentrated')
            quit()
        if Character.is_hasted:
            print('Still Hasted')
            quit()
        Character.start_of_turn()
        if Character.action != 0 or Character.bonus_action != 0 or Character.attack_counter != 0:
            print('Should be exhaused from haste')
            quit()
        else:
            print('Haste Round Test')
            return True

def HexTest(Character, Enemy):
    Character.SpellBook['Hex'].is_known = True
    Character.spell_slot_counter[0] = 1
    Character.SpellBook['Hex'].cast([Enemy])
    if Character.is_concentrating == False: 
        print('Not Concentrated after cast')
        quit()
    else:
        Enemy.unconscious()
        if Character.is_concentrating == False:
            print('Why lost con')
            quit()
        else:
            if Character.can_choose_new_hex == True:
                print('Hex Test')
                return True

def HexConTest(Character, Enemy):
    Character.SpellBook['Hex'].is_known = True
    Character.spell_slot_counter[0] = 1
    Character.SpellBook['Hex'].cast([Enemy])
    if Character.is_concentrating == False: 
        print('Not Concentrated after cast')
        quit()
    else:
        Character.CHP = 200
        Character.changeCHP(dmg(100, 'true'), Enemy, was_ranged = False)
        if Character.is_hexing == True:
            print('Still Hexing after break Con')
            quit()
        if Character.can_choose_new_hex == True:
            print('should not choose a new Hex')
            quit()
        if Character.CurrentHexToken != False:
            print('should not still have Hex Token')
            quit()
        if Enemy.is_hexed:
            print('Still Hexed after break Con')
            quit()
        print('Hex Break Concentration Test')

def HexSwitchTest(Character, Enemy1, Enemy2):
    Character.SpellBook['Hex'].is_known = True
    Character.spell_slot_counter[0] = 1
    Character.SpellBook['Hex'].cast([Enemy1])
    Enemy1.unconscious()
    Enemy2.CHP = 100
    Character.end_of_turn()
    Character.AI.do_your_turn(fight)
    if Enemy2.is_hexed == False:
        print('Not changed Targets')
        print(Enemy2.is_hexed)
        for x in Enemy2.TM.TokenList:
            print(x.subtype)
        Enemy2.TM.update()
        print(Enemy2.is_hexed)
        quit()
    print('Hex switching Test')

def conjureAnimalsTest(Character):
    TestFight = [Character]
    Character.SpellBook['ConjureAnimals'].is_known = True
    Character.spell_slot_counter[2] = 1
    Character.SpellBook['ConjureAnimals'].cast(TestFight)
    Character.CHP = 200
    Character.changeCHP(dmg(100, 'true'), Enemy, was_ranged = False)
    if Character.is_concentrating:
        print('Still concentrated')
        quit()
    if Character.has_summons:
        print('Has still summons')
        quit()
    for x in TestFight:
        if x.state != -1 and x != Character:
            print('Not all Summons vanish')
            print(len(TestFight))
            print([x.name for x in TestFight])
            print([x.state for x in TestFight])
            quit()
    for x in TestFight:
        if x != Character and x.is_summoned == False:
            print('Not all summons are summons')
            quit()
    Character.end_of_turn()
    Character.spell_slot_counter[2] = 1
    Character.SpellBook['ConjureAnimals'].cast(TestFight)
    for x in TestFight:
        if x != Character: x.death()
    if Character.is_concentrating:
        print('Still concentrated after all summons')
        quit()
    if Character.has_summons:
        print('Has still summons but all dead')
        quit()
    print('Conjure Animals Test')

def guidingBoltTest(Character, Enemy):
    Character.SpellBook['GuidingBolt'].is_known = True
    Character.spell_slot_counter[0] = 1
    Character.SpellBook['GuidingBolt'].cast(Enemy)
    if len(Character.TM.TokenList) == 0:
        print('Not Guiding Bolting')
        quit()
    if len(Enemy.TM.TokenList) == 0:
        print('Not Guiding Bolted')
        quit()
    Character.action = 1
    Character.attack(Enemy)

    if len(Character.TM.TokenList) != 0:
        print('Still Guiding Bolting')
        quit()
    if len(Enemy.TM.TokenList) != 0:
        print('Still Guiding Bolted')
        quit()
    print('Guiding Bolt Test')




if __name__ == '__main__':
    DM = DungeonMaster()
    DM.enable_print()
    Character = entity('Ape', 0, DM, archive=True)
    Character.orignial_name = 'Hero'
    Character2 = entity('Ape', 0, DM, archive=True)
    Character3 = entity('Ape', 0, DM, archive=True)
    Enemy = entity('Ape', 1, DM, archive=True)
    Enemy.orignial_name = 'Enemy'
    Enemy2 = entity('Ape', 1, DM, archive=True)
    Enemy3 = entity('Ape', 1, DM, archive=True)

    fight = [Character, Character2, Character3, Enemy, Enemy2, Enemy3]

    #Concentration Test
    reset(fight)
    ConcentrationTest1(Character, Enemy)
    reset(fight)
    ConcentrationTestEntangle(Character, Enemy)
    reset(fight)
    HasteRoundTest(Character)
    reset(fight)
    HexTest(Character, Enemy)
    reset(fight)
    HexConTest(Character, Enemy)
    reset(fight)
    HexSwitchTest(Character, Enemy, Enemy2)
    reset(fight)
    conjureAnimalsTest(Character)