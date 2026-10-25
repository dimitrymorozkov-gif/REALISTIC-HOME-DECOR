"""Curated parametric furniture. Units are 1/16 metre; north is the front."""

def box(x1, y1, z1, x2, y2, z2, material='wood', end=None):
    return (x1, y1, z1, x2, y2, z2, material) + ((end,) if end else ())

def legs(w=16, d=16, h=10, t=1.5, inset=1.5, material='wood'):
    return [box(x, 0, z, x+t, h, z+t, material) for x in (inset, w-inset-t) for z in (inset, d-inset-t)]

def table(w=16, d=16, h=12, thickness=1.5, style='four', top='wood'):
    b = [box(.5, h-thickness, .5, w-.5, h, d-.5, top)]
    if style == 'pedestal':
        b += [box(w/2-2, .5, d/2-2, w/2+2, h-thickness, d/2+2, 'metal'), box(w/2-6, 0, d/2-5, w/2+6, 1, d/2+5, 'metal')]
    elif style == 'trestle':
        for x in (2, w-4):
            b += [box(x, 0, 2, x+2, 1.5, d-2, 'metal'), box(x+.5, 1.5, 3, x+1.5, h-thickness, d-3, 'metal')]
        b += [box(3, 4, d/2-.6, w-3, 5, d/2+.6, 'metal')]
    else:
        b += legs(w,d,h-thickness)
        b += [box(2.5, h-3.5, 2.5, w-2.5, h-1.5, 3.5), box(2.5, h-3.5, d-3.5, w-2.5, h-1.5, d-2.5)]
    return b

def chair(w=14, d=14, seat=7.5, back=16, arms=False, style='slat'):
    b = legs(w,d,seat-1.5,1.25,1.25)
    b += [box(1,seat-1.5,1,w-1,seat,d-1,'wood'),box(1.5,seat,1.5,w-1.5,seat+1,d-3,'fabric')]
    b += [box(1,seat,d-2.5,2.2,back-4,d-1),box(w-2.2,seat,d-2.5,w-1,back-4,d-1)]
    if style == 'slat':
        b += [box(1.5,back-4,d-2.5,w-1.5,back,d-1,'wood')]
        for x in (3,6,9): b += [box(x,seat+2,d-2.1,x+.7,back-4,d-1.4,'wood')]
    else:
        b += [box(2,seat+1,d-3,w-2,back-1,d-1.5,'fabric')]
    if arms:
        for x in (0,w-1):
            b += [box(x,seat+3,2,x+1,seat+4,d-1,'wood'), box(x,seat,2,x+1,seat+3,3,'metal')]
    return b

def sofa(w=32, d=16, sections=2, modular=False):
    b=legs(w,d,2,1.5,2,'metal')+[box(.5,2,.5,w-.5,4,d-.5,'wood'),box(1,4,d-4,w-1,13.5,d-1,'fabric')]
    for n in range(sections):
        x=2+n*(w-4)/sections
        b += [box(x,4,1.5,x+(w-4)/sections-.4,7,d-4,'fabric'),box(x+.3,8,d-4.8,x+(w-4)/sections-.7,13,d-2.5,'accent')]
    b += [box(.5,4,1,2,10,d-4,'fabric','left' if modular else None),box(w-2,4,1,w-.5,10,d-4,'fabric','right' if modular else None)]
    return b

def cabinet(w=16,d=16,h=14,sections=2,top=True,glass=False):
    b = [box(.5,1,1.5,w-.5,h-1,d-.5),box(1,0,2,w-1,1,d-1,'metal')]
    if glass:
        b = [box(.5,1,1.5,1.5,h-1,d-.5),box(w-1.5,1,1.5,w-.5,h-1,d-.5),box(1.5,1,d-1.5,w-1.5,h-1,d-.5),box(1.5,1,1.5,w-1.5,2,d-1.5),box(1,0,2,w-1,1,d-1,'metal'),box(.5,h-2,1.5,w-.5,h-1,d-.5)]
    if top: b += [box(0,h-1,0,w,h,d,'stone')]
    for n in range(sections):
        x=.8+n*(w-1.6)/sections
        b += [box(x,2,1,x+(w-1.6)/sections-.3,h-1.5,1.6,'glass' if glass else 'accent'),box(x+1,h-4,0,x+1.5,h-2.2,.9,'metal')]
    return b

def toilet(wall=False):
    b=[box(4,0,5,12,2,13,'ceramic'),box(5,2,5,11,6,13,'ceramic'),box(3,6,2,13,9,13,'ceramic'),box(4,8,1.5,12,10,12,'ceramic'),box(5,9.9,3,11,10.1,10,'screen'),box(3.5,10,2,12.5,10.6,3,'accent'),box(3.5,10,10.5,12.5,10.6,12,'accent'),box(3.5,10,3,4.5,10.6,10.5,'accent'),box(11.5,10,3,12.5,10.6,10.5,'accent')]
    if not wall: b += [box(3,9,12,13,15.5,15,'ceramic'),box(3,15.5,11.8,13,15.8,15.3,'ceramic'),box(6,15.9,13,10,16,14,'metal')]
    return b

def sink(w=16,d=16,stand=True):
    b=cabinet(w,d,11,2) if stand else []
    b += [box(1,11,2,w-1,12.5,d-2,'ceramic'),box(1,12.5,2,2,14,d-2,'ceramic'),box(w-2,12.5,2,w-1,14,d-2,'ceramic'),box(2,12.5,2,w-2,14,3,'ceramic'),box(2,12.5,d-3,w-2,14,d-2,'ceramic'),box(w/2-1,11,d-1.5,w/2,15,d-.5,'metal'),box(w/2-1,15,d-6,w/2,16,d-.5,'metal')]
    return b

def lamp(floor=False):
    h=30 if floor else 12
    return [box(4,0,4,12,1,12,'metal'),box(7,1,7,9,h-6,9,'metal'),box(3,h-6,3,13,h-1,13,'fabric'),box(3.5,h-1,3.5,12.5,h,12.5,'accent'),box(5,h-6.2,5,11,h-6,11,'light')]

def bookshelf(w=16,h=32):
    b=[box(0,0,1,1,h,15),box(w-1,0,1,w,h,15),box(1,0,14,w-1,h,15)]
    for y in range(0,h+1,8):
        b+=[box(1,min(y,h-1),1,w-1,min(y,h-1)+1,14)]
        if y<h-4:
            for j in range(5):
                x=2+j*(w-4)/5
                b += [box(x,y+1,6,x+1.5,y+5+j%3,13,'book' if j%2 else 'accent')]
    return b

def bed(w=16,d=32):
    b=legs(w,d,3,2,1.5)+[box(0,2,0,w,5,d-2),box(1,5,1,w-1,8,d-3,'fabric'),box(1,8,2,w-1,8.5,d-8,'accent'),box(0,3,d-2,w,16,d,'wood')]
    for x in range(2,w-3,7): b += [box(x,8,d-8,min(x+6,w-2),10,d-3,'fabric')]
    b+=[box(1,6,d-2.3,w-1,14,d-1.3,'fabric')]
    return b

def designs():
    out=[]
    def add(i,en,ru,cat,b,placement='floor',luminance=0,connect=False,**params):
        out.append(dict(id=i,en=en,ru=ru,category=cat,placement=placement,luminance=luminance,connect=connect,params=params,boxes=b))
    add('modern_chair','Modern chair','Современный стул','kitchen',chair(),width=14,depth=14,seat_height=7.5,back='slat',arms=False)
    add('dining_table','Dining table','Обеденный стол','kitchen',table(32,16,12),width=32,depth=16,height=12,legs='four')
    add('modern_sofa','Two-seat sofa','Двухместный диван','living_room',sofa(),width=32,sections=2)
    add('kitchen_cabinet','Kitchen cabinet','Кухонный шкаф','kitchen',cabinet(),width=16,sections=2)
    add('toilet','Modern toilet','Современный унитаз','bathroom',toilet())
    add('armchair','Upholstered armchair','Мягкое кресло','living_room',sofa(16,16,1),width=16,sections=1)
    add('coffee_table','Low coffee table','Журнальный столик','living_room',table(24,16,7,1,'trestle'),width=24,height=7,legs='trestle')
    add('computer_desk','Computer desk','Компьютерный стол','office',[table(32,16,12,1.25,'trestle')[0]]+table(32,16,12,1.25,'trestle')[3:]+cabinet(10,12,10,1,False),width=32,height=12,legs='trestle')
    add('single_bed','Single bed','Односпальная кровать','bedroom',bed(),width=16,depth=32)
    add('nightstand','Bedside table','Прикроватная тумба','bedroom',legs(12,12,2)+[box(0,2,.8,12,9,12),box(.5,3,.3,11.5,5.5,.8,'accent'),box(.5,6,.3,11.5,8.5,.8,'accent'),box(4,4,0,8,4.7,.3,'metal'),box(4,7,0,8,7.7,.3,'metal')],width=12,height=9)
    add('wardrobe','Wardrobe','Гардеробный шкаф','bedroom',cabinet(32,16,32,4,False)+[box(0,31,0,32,32,16)],width=32,height=32,sections=4)
    add('refrigerator','Refrigerator','Холодильник','kitchen',[box(1,1,1,15,31,15,'metal'),box(1.3,1,.7,14.7,18,1.3,'accent'),box(1.3,18.5,.7,14.7,30,1.3,'accent'),box(12,13,0,13,17,.7,'metal'),box(12,20,0,13,24,.7,'metal'),box(3,0,2,5,1,4,'metal'),box(11,0,12,13,1,14,'metal')],height=31)
    add('stove','Decorative cooker','Декоративная плита','kitchen',cabinet()+[box(2,3,0,14,10,.7,'screen'),box(3,10.5,.2,13,11.3,1.4,'metal'),box(2,13.9,2,6,14.2,6,'metal'),box(10,13.9,2,14,14.2,6,'metal'),box(2,13.9,10,6,14.2,14,'metal'),box(10,13.9,10,14,14.2,14,'metal')])
    add('vanity_sink','Vanity sink','Раковина с тумбой','bathroom',sink())
    add('bathtub','Freestanding bathtub','Отдельностоящая ванна','bathroom',[box(2,0,2,14,2,30,'metal'),box(1,2,1,15,4,31,'ceramic'),box(1,4,1,3,11,31,'ceramic'),box(13,4,1,15,11,31,'ceramic'),box(3,4,1,13,11,3,'ceramic'),box(3,4,29,13,11,31,'ceramic'),box(.5,10.5,.5,3.5,12,31.5,'ceramic'),box(12.5,10.5,.5,15.5,12,31.5,'ceramic'),box(3.5,10.5,.5,12.5,12,3.5,'ceramic'),box(3.5,10.5,28.5,12.5,12,31.5,'ceramic'),box(6,4,23,7,4.1,24,'metal'),box(13,11,22,14,16,23,'metal'),box(10,15,22,14,16,23,'metal')],depth=32)
    add('shower_cabin','Shower enclosure','Душевая кабина','bathroom',[box(0,0,0,16,1.5,16,'ceramic'),box(0,1.5,15,16,32,16,'stone'),box(0,1.5,.7,.7,31,15,'glass'),box(15.3,1.5,.7,16,31,15,'glass'),box(0,1.5,0,.7,32,.7,'metal'),box(15.3,1.5,0,16,32,.7,'metal'),box(0,31,0,16,32,1,'metal'),box(7.5,14,14,8.5,28,15,'metal'),box(7.5,28,10,8.5,29,15,'metal'),box(5,27.5,8,11,28.5,12,'metal'),box(6,27.4,8.5,10,27.6,11.5,'screen'),box(7,12,14,10,13,15.5,'metal')],height=32)
    add('television','Flat-screen television','Плоский телевизор','living_room',[box(0,5,10,32,24,12,'metal'),box(1,6,9.8,31,23,10,'screen'),box(14,1,10,18,5,12,'metal'),box(8,0,7,24,1,14,'metal'),box(29,5.4,9.6,30,5.8,10,'light')],width=32)
    add('table_lamp','Table lamp','Настольная лампа','lighting',lamp(),luminance=12)
    add('floor_lamp','Floor lamp','Торшер','lighting',lamp(True),luminance=14)
    add('bookshelf','Bookcase','Книжный стеллаж','living_room',bookshelf(),height=32)
    # Further designs expand geometry and silhouettes, not just the colour count.
    add('modular_sofa','Modular sofa section','Секция модульного дивана','living_room',sofa(16,16,1,True),connect=True,width=16,sections=1)
    add('corner_sofa','Corner sofa','Угловой диван','living_room',sofa(32,16,2)+[box(16,2,16,32,4,32),box(18,4,16,30,7,30,'fabric'),box(29,4,16,32,13,32,'fabric'),box(17,0,28,19,2,30,'metal'),box(29,0,28,31,2,30,'metal')],width=32,depth=32)
    add('ottoman','Upholstered ottoman','Мягкий пуф','living_room',legs(12,12,2,1.5,1)+[box(0,2,0,12,5,12),box(.3,5,.3,11.7,8,11.7,'fabric'),box(1,7.8,1,11,8.2,11,'accent')])
    add('wall_shelf','Floating wall shelf','Навесная полка','living_room',[box(0,3,10,16,4.5,16),box(2,0,14.5,3,3,16,'metal'),box(13,0,14.5,14,3,16,'metal')],placement='wall')
    add('tv_console','TV console','Тумба под телевизор','living_room',cabinet(32,14,8,4,False),width=32,sections=4)
    add('upper_cabinet','Wall kitchen cabinet','Навесной кухонный шкаф','kitchen',cabinet(16,8,16,2,False),placement='wall',width=16,height=16)
    add('glass_cabinet','Glass-front cabinet','Шкаф с витриной','kitchen',cabinet(16,12,24,2,False,True)+[box(1,8,1,15,9,11),box(1,16,1,15,17,11)],height=24)
    add('kitchen_island','Kitchen island','Кухонный остров','kitchen',cabinet(32,16,14,4)+[box(0,13,16,32,14,24,'stone'),box(2,0,21,3.5,13,22.5,'metal'),box(28.5,0,21,30,13,22.5,'metal')],width=32,depth=24)
    add('bar_stool','Bar stool','Барный стул','kitchen',chair(12,12,12,20,False,'upholstered')+[box(1,4,1,11,5,2,'metal'),box(1,4,10,11,5,11,'metal')],seat_height=12)
    add('kettle','Electric kettle','Электрический чайник','kitchen',[box(4,0,4,12,1,12,'metal'),box(5,1,5,11,7,11,'ceramic'),box(5.5,7,5.5,10.5,8,10.5,'metal'),box(11,2,5,12,6,6,'metal'),box(12,2,5,13,3,10,'metal'),box(12,5,5,13,6,10,'metal'),box(12,3,9,13,5,10,'metal'),box(3,4,5,5,6,7,'metal')])
    add('coffee_machine','Coffee machine','Кофемашина','kitchen',[box(3,0,3,13,1,13,'metal'),box(4,1,9,12,12,13,'accent'),box(4,9,4,12,12,9,'metal'),box(5,8,5,11,9,8,'screen'),box(7,6,5,9,8,7,'metal'),box(6,1,5,10,3,9,'ceramic'),box(10,1.5,6,11,2.5,8,'ceramic'),box(5,10,3.8,7,11,4,'screen')])
    add('wall_sink','Wall-mounted basin','Подвесная раковина','bathroom',sink(16,12,False),placement='wall')
    add('washing_machine','Washing machine','Стиральная машина','bathroom',cabinet()+[box(4,3,0,12,10,.7,'metal'),box(5,4,.1,11,9,.3,'glass'),box(2,11,0,6,12,.8,'screen'),box(11,11,0,13,13,.8,'metal')])
    add('double_bed','Double bed','Двуспальная кровать','bedroom',bed(32,32),width=32,depth=32)
    add('dresser','Chest of drawers','Комод','bedroom',[box(.5,1,1.5,23.5,11,11.5),box(1,0,2,23,1,11,'metal'),box(0,11,0,24,12,12,'stone')]+[b for y in (2,5,8) for b in (box(.8,y,.7,23.2,y+2.5,1.2,'accent'),box(10,y+1,0,14,y+1.7,.7,'metal'))],width=24)
    add('vanity_table','Dressing table','Туалетный столик','bedroom',table(24,12,12)+[box(5,12,10,19,25,11,'metal'),box(6,13,9.8,18,24,10,'glass')],width=24)
    add('office_chair','Office chair','Офисное кресло','office',[box(2,0,6.5,14,1,8,'metal'),box(7,0,2,8.5,1,14,'metal'),box(6.5,1,6.5,9,6,9,'metal'),box(2,6,2,14,8,14,'fabric'),box(3,8,12,13,20,14,'fabric'),box(1,10,3,2.5,11,12,'metal'),box(13.5,10,3,15,11,12,'metal'),box(1,7,10,2,10,12,'metal'),box(14,7,10,15,10,12,'metal')])
    add('desktop_monitor','Desktop monitor','Компьютерный монитор','office',[box(1,4,8,15,14,9.5,'metal'),box(1.7,4.7,7.8,14.3,13.3,8,'screen'),box(7,1,8,9,4,9,'metal'),box(4,0,5,12,1,11,'metal'),box(3,0,0,13,.5,3,'accent')])
    add('coat_rack','Hallway coat rack','Напольная вешалка','decorations',[box(3,0,3,13,1,13),box(7,1,7,9,27,9),box(2,23,7,14,24,9,'metal'),box(2,24,7,3,26,9,'metal'),box(13,24,7,14,26,9,'metal'),box(7,19,3,9,20,13,'metal'),box(7,20,3,9,22,4,'metal'),box(7,20,12,9,22,13,'metal')])
    return out
