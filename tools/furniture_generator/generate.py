#!/usr/bin/env python3
"""Deterministic, dependency-free furniture resource compiler for Minecraft 1.21.11.

Generated paths are tracked by SHA256. Hand edits are never overwritten unless
--force is explicitly requested. Edit templates/materials, then regenerate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

from templates import designs as furniture_designs
from extras import designs as extra_designs

ROOT = Path(__file__).resolve().parents[2]
NS = 'realistic_home_decor'
ASSET = Path('src/main/resources/assets') / NS
DATA = Path('src/main/resources/data') / NS
MANIFEST = Path('tools/furniture_generator/generated_manifest.json')
CATEGORIES = ['living_room','kitchen','bathroom','bedroom','office','lighting','architecture','building_materials','decorations','outdoor','garage']
CATEGORY_NAMES = {
    'living_room': ('Living Room','Гостиная'), 'kitchen': ('Kitchen','Кухня'),
    'bathroom': ('Bathroom','Ванная'), 'bedroom': ('Bedroom','Спальня'),
    'office': ('Office','Кабинет'), 'lighting': ('Lighting','Освещение'),
    'architecture': ('Architecture','Архитектура'), 'building_materials': ('Building Materials','Строительные материалы'),
    'decorations': ('Decorations','Декор'), 'outdoor': ('Outdoor','Сад и терраса'), 'garage': ('Garage','Гараж'),
}
# Each material is shared across the collection; all artwork is generated here.
MATERIALS = {
    'light_oak': ('wood',(185,146,98)), 'dark_oak': ('wood',(89,64,43)),
    'walnut': ('wood',(110,72,50)), 'pine': ('wood',(207,171,119)),
    'birch': ('wood',(215,199,156)), 'bleached_wood': ('wood',(224,217,198)),
    'ebony': ('wood',(40,39,36)), 'natural_veneer': ('wood',(160,120,82)),
    'white_marble': ('stone',(224,224,218)), 'black_marble': ('stone',(42,44,45)),
    'grey_marble': ('stone',(130,133,130)), 'granite': ('granite',(142,137,129)),
    'travertine': ('stone',(194,179,151)), 'decorative_stone': ('granite',(157,148,133)),
    'stainless_steel': ('metal',(151,161,163)), 'chrome': ('metal',(198,207,207)),
    'black_metal': ('metal',(42,45,46)), 'matte_metal': ('matte',(103,111,113)),
    'brass': ('metal',(172,136,63)), 'aluminium': ('metal',(185,191,190)),
    'cotton': ('fabric',(202,197,180)), 'linen': ('fabric',(188,180,156)),
    'velvet': ('fabric',(77,99,100)), 'light_upholstery': ('fabric',(217,210,195)),
    'dark_upholstery': ('fabric',(66,73,76)), 'leather': ('leather',(119,76,49)),
    'faux_leather': ('leather',(53,56,53)), 'ceramic': ('gloss',(226,228,221)),
    'glass': ('glass',(166,205,215)), 'matte_plastic': ('matte',(64,70,73)),
    'glossy_plastic': ('gloss',(213,218,212)), 'concrete': ('granite',(151,151,143)),
    'plaster': ('matte',(220,215,202)), 'screen': ('screen',(24,42,50)),
    'leaf': ('leaf',(65,110,64)), 'warm_light': ('gloss',(255,235,183)),
    'book_pages': ('paper',(223,210,177)),
}
PALETTES = {
 'oak': dict(en='Natural oak',ru='Натуральный дуб',wood='light_oak',fabric='linen',stone='white_marble',metal='black_metal',accent='velvet'),
 'walnut': dict(en='Walnut & brass',ru='Орех и латунь',wood='walnut',fabric='leather',stone='travertine',metal='brass',accent='cotton'),
 'ebony': dict(en='Ebony & charcoal',ru='Эбен и графит',wood='ebony',fabric='dark_upholstery',stone='black_marble',metal='stainless_steel',accent='matte_plastic'),
 'ivory': dict(en='Ivory & birch',ru='Слоновая кость и берёза',wood='bleached_wood',fabric='light_upholstery',stone='grey_marble',metal='chrome',accent='birch'),
}
FIXED = dict(ceramic='ceramic',glass='glass',screen='screen',leaf='leaf',light='warm_light',book='book_pages',concrete='concrete')


def encode(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()


def png(width,height,pixels):
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    raw=b''.join(b'\0'+bytes(pixels[y*width*4:(y+1)*width*4]) for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')


def texture(name,kind,rgb,size=64):
    seed=int.from_bytes(hashlib.sha256(name.encode()).digest()[:4],'big')
    pixels=[]
    for y in range(size):
        for x in range(size):
            n=((x*73856093 ^ y*19349663 ^ seed)*83492791)&0xffffffff
            jitter=(n%13)-6
            delta=jitter/2
            alpha=255
            if kind=='wood': delta += 5*math.sin(x*.62+math.sin(y*.13)*1.2)+3*math.sin(x*.17+y*.035)
            elif kind=='stone': delta += 12 if abs(math.sin(x*.11+y*.16+math.sin(y*.18)*.8))>.965 else 0
            elif kind=='granite': delta += (n%37)-18
            elif kind=='fabric': delta += (2 if x%2 else -2)+(2 if y%2 else -2)
            elif kind=='metal': delta += math.sin(x*.10)*7+(2 if y%4==0 else 0)
            elif kind=='leather': delta += ((n>>8)%7)-3
            elif kind=='glass':
                delta = 18 if x in (1,2,60,61) or y in (1,2,60,61) else (4 if (x+y)%29<2 else 0)
                alpha=160 if delta else 72
            elif kind=='screen': delta += 8*(x+y)/size+(4 if y%3==0 else 0)
            elif kind=='leaf': delta += ((x//4+y//5)%3)*7
            elif kind=='paper': delta += -12 if y%5==0 else 1
            elif kind=='gloss': delta += 5*(1-x/size)
            pixels.extend([max(0,min(255,round(v+delta))) for v in rgb]+[alpha])
    return png(size,size,pixels)


def rounded(v):
    v=round(v,5)
    return int(v) if int(v)==v else v


def cube_element(cube,scale=1.0,cull=False):
    a=[rounded(cube[i]*scale) for i in range(3)]
    b=[rounded(cube[i+3]*scale) for i in range(3)]
    dx,dy,dz=[max(.001,b[i]-a[i]) for i in range(3)]
    dims={'north':(dx,dy),'south':(dx,dy),'west':(dz,dy),'east':(dz,dy),'up':(dx,dz),'down':(dx,dz)}
    faces={face:{'uv':[0,0,rounded(min(16,w)),rounded(min(16,h))],'texture':'#'+cube[6]} for face,(w,h) in dims.items()}
    if cull:
        for face,axis,edge in [('north',2,0),('south',2,16),('west',0,0),('east',0,16),('down',1,0),('up',1,16)]:
            if (a[axis] if edge==0 else b[axis])==edge:
                faces[face]['cullface']=face
    return {'from':a,'to':b,'faces':faces}


def clipped(cubes,offset):
    result=[]
    lo=[n*16 for n in offset]
    hi=[n+16 for n in lo]
    for b in cubes:
        a=[max(b[i],lo[i]) for i in range(3)]
        c=[min(b[i+3],hi[i]) for i in range(3)]
        if all(c[i]>a[i]+.00001 for i in range(3)):
            result.append(tuple(rounded(v-lo[i]) for i,v in enumerate(a))+tuple(rounded(v-lo[i]) for i,v in enumerate(c))+b[6:])
    return result


def collision(cubes):
    # Exclude handles and other tiny details. Retain independent legs and open
    # spaces instead of replacing a chair/table with a solid bounding cube.
    def volume(b): return math.prod(b[i+3]-b[i] for i in range(3))
    significant=[b for b in cubes if volume(b)>=2]
    selected=sorted(significant,key=volume,reverse=True)[:12]
    return [list(b[:6]) for b in sorted(selected,key=lambda b:tuple(b[:6]))]


def visible(cubes,left=False,right=False):
    return [b for b in cubes if len(b)<8 or not ((b[7]=='left' and left) or (b[7]=='right' and right))]


def icon():
    pixels=[]
    for y in range(128):
        for x in range(128):
            color=(27,43,45,255)
            if 18<x<111 and 70<y<89: color=(183,145,97,255)
            if (23<x<28 or 99<x<104) and 89<=y<110: color=(179,142,91,255)
            if (18<x<33 or 96<x<111) and 54<y<76: color=(110,141,133,255)
            if 32<x<97 and 43<y<74: color=(118,151,141,255)
            if 36<x<62 and 72<y<80 or 66<x<93 and 72<y<80: color=(209,200,174,255)
            if 23<y<27 and 25<x<103: color=(226,208,157,255)
            pixels.extend(color)
    return png(128,128,pixels)


def all_designs():
    collection=furniture_designs()+extra_designs()
    # Ensure wall-mounted cabinet carcasses meet their supporting plane.
    for d in collection:
        if d['id'] in ('upper_cabinet','wall_sink'):
            dz=16-max(b[5] for b in d['boxes'])
            d['boxes']=[b[:2]+(b[2]+dz,)+b[3:5]+(b[5]+dz,)+b[6:] for b in d['boxes']]
        if d['id'] in ('kitchen_cabinet','upper_cabinet'):
            d['connect']=True
        if d['id']=='parquet_floor':
            d['en']='Plank parquet panel'; d['ru']='Панель дощатого паркета'
    return collection


def compile_resources(stage='full'):
    output={}
    def put(path,value): output[str(path)]=value if isinstance(value,bytes) else encode(value)
    collection=all_designs()
    if stage=='first-five': collection=collection[:5]
    elif stage=='first-twenty': collection=collection[:20]
    for name,(kind,color) in MATERIALS.items(): put(ASSET/'textures/block'/f'{name}.png',texture(name,kind,color))
    put(ASSET/'icon.png',icon())
    entries=[]; locales={'en_us':{},'ru_ru':{}}
    for cat,names in CATEGORY_NAMES.items():
        for language,text in zip(('en_us','ru_ru'),names): locales[language][f'itemGroup.{NS}.{cat}']=text
    locales['en_us'][f'message.{NS}.no_space']='Not enough space for this furniture.'
    locales['ru_ru'][f'message.{NS}.no_space']='Недостаточно места для этой мебели.'
    default_tex={role:f'{NS}:block/{mat}' for role,mat in (FIXED|{k:v for k,v in PALETTES['oak'].items() if k not in ('en','ru')}).items()}
    for design in collection:
        boxes=design['boxes']; template=design['id']; connected=design['connect']
        assert template and boxes and all(all(b[i+3]>b[i]>=0 for i in range(3)) for b in boxes),template
        dimensions=[math.ceil(max(b[i+3] for b in boxes)/16) for i in range(3)]
        offsets=[(x,y,z) for y in range(dimensions[1]) for z in range(dimensions[2]) for x in range(dimensions[0]) if clipped(boxes,(x,y,z))]
        assert (0,0,0) in offsets,template
        assert not connected or len(offsets)==1,f'Connections currently require a single cell: {template}'
        for index,offset in enumerate(offsets):
            cell=clipped(boxes,offset)
            for left,right in ((False,False),(True,False),(False,True),(True,True)) if connected else [(False,False)]:
                tag=f'_l{int(left)}r{int(right)}' if connected else ''
                suffix=f'_part_{index}' if index else ''
                put(ASSET/'models/block'/f'{template}_shape{suffix}{tag}.json',{'ambientocclusion':True,'textures':default_tex|{'particle':default_tex['wood']},'elements':[cube_element(b,cull=True) for b in visible(cell,left,right)]})
        # Inventory models contain the entire object. Normalize all axes equally
        # into one model cube so large furniture never exceeds vanilla bounds.
        scale=min(1,16/max(max(b[i+3] for b in boxes) for i in range(3)))
        put(ASSET/'models/item'/f'{template}_shape.json',{'parent':'minecraft:block/block','textures':default_tex|{'particle':default_tex['wood']},'elements':[cube_element(b,scale) for b in boxes],
          'display':{'gui':{'rotation':[30,225,0],'translation':[0,0,0],'scale':[.8,.8,.8]},'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[.4,.4,.4]},'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[.65,.65,.65]}}})
        for palette,values in PALETTES.items():
            identifier=f'{template}_{palette}'
            tex={role:f'{NS}:block/{mat}' for role,mat in (FIXED|{k:v for k,v in values.items() if k not in ('en','ru')}).items()}
            parts=[]
            for index,offset in enumerate(offsets):
                suffix=f'_part_{index}' if index else ''
                part_id=identifier+suffix; cell=clipped(boxes,offset)
                part={'id':part_id,'offset':list(offset),'boxes':collision(cell)}
                if connected:
                    part['connection_boxes']={f'{str(l).lower()}_{str(r).lower()}':collision(visible(cell,l,r)) for l,r in ((False,False),(True,False),(False,True),(True,True))}
                parts.append(part)
                variants={}
                for left,right in ((False,False),(True,False),(False,True),(True,True)) if connected else [(False,False)]:
                    tag=f'_l{int(left)}r{int(right)}' if connected else ''
                    model_id=part_id+tag
                    put(ASSET/'models/block'/f'{model_id}.json',{'parent':f'{NS}:block/{template}_shape{suffix}{tag}','textures':tex|{'particle':tex['wood']}})
                    for facing,angle in zip(('north','east','south','west'),(0,90,180,270)):
                        key=f'facing={facing}'+(f',left={str(left).lower()},right={str(right).lower()}' if connected else '')
                        variants[key]={'model':f'{NS}:block/{model_id}','y':angle,'uvlock':False}
                put(ASSET/'blockstates'/f'{part_id}.json',{'variants':variants})
                loot={'type':'minecraft:block','pools':[]}
                if index==0: loot['pools']=[{'rolls':1,'entries':[{'type':'minecraft:item','name':f'{NS}:{identifier}'}],'conditions':[{'condition':'minecraft:survives_explosion'}]}]
                put(DATA/'loot_table/blocks'/f'{part_id}.json',loot)
            put(ASSET/'models/item'/f'{identifier}.json',{'parent':f'{NS}:item/{template}_shape','textures':tex|{'particle':tex['wood']}})
            put(ASSET/'items'/f'{identifier}.json',{'model':{'type':'minecraft:model','model':f'{NS}:item/{identifier}'}})
            names={lang:f"{design[key]} — {values[lang[:2] if lang=='en_us' else 'ru']}" for lang,key in [('en_us','en'),('ru_ru','ru')]}
            for language,name in names.items(): locales[language][f'block.{NS}.{identifier}']=name
            entries.append({'id':identifier,'template':template,'category':design['category'],'names':names,'placement':design['placement'],'luminance':design['luminance'],'connect':connected,'material':palette,'render_layer':'translucent' if any(b[6]=='glass' for b in boxes) else 'solid','parts':parts})
    put(DATA/'catalog.json',{'schema_version':1,'entries':entries})
    for language,locale in locales.items(): put(ASSET/'lang'/f'{language}.json',locale)
    put(Path('tools/furniture_generator/materials/materials.json'),{'materials':{name:{'pattern':kind,'rgb':list(color),'resolution':64,'texture':f'{NS}:block/{name}'} for name,(kind,color) in MATERIALS.items()},'palettes':PALETTES})
    catalog=['# Каталог Realistic Home Decor','',f'{len(collection)} разных конструкций × {len(PALETTES)} согласованных палитры = **{len(entries)} предметов**.','', 'Палитры: натуральный дуб; орех и латунь; эбен и графит; слоновая кость и берёза.','', '| ID конструкции | English | Русский | Категория | Ячеек |','|---|---|---|---|---:|']
    for d in collection:
        n=len(next(e for e in entries if e['template']==d['id'])['parts'])
        catalog.append(f"| `{d['id']}` | {d['en']} | {d['ru']} | {d['category']} | {n} |")
    catalog+=['','Полный ID предмета: `realistic_home_decor:<конструкция>_<палитра>`. Например: `realistic_home_decor:modern_chair_oak`.','', 'Мебель декоративная. Крупная мебель занимает перечисленные ячейки; модели и коллизии разбиты по ячейкам. Поддерживаются повороты на 90°. Секции дивана, кухонные и навесные шкафы, стеновые панели и перила соединяются с такой же конструкцией и палитрой при одинаковом направлении.']
    put(Path('docs/CATALOG.md'),('\n'.join(catalog)+'\n').encode())
    return output,entries


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='compare generated resources without writing')
    parser.add_argument('--force',action='store_true',help='explicitly overwrite changed generated files')
    parser.add_argument('--stage',choices=('first-five','first-twenty','full'),default='full')
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args(argv)
    root=args.root.resolve()
    output,entries=compile_resources(args.stage)
    manifest_path=root/MANIFEST
    previous=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    failures=[]
    for relative,content in output.items():
        p=root/relative
        if args.check:
            if not p.exists() or p.read_bytes()!=content: failures.append(f'outdated/missing: {relative}')
        elif p.exists() and p.read_bytes()!=content and (relative not in previous or hashlib.sha256(p.read_bytes()).hexdigest()!=previous[relative]) and not args.force:
            failures.append(f'hand-edited generated file (use --force deliberately): {relative}')
    stale=set(previous)-set(output)
    for relative in stale:
        p=root/relative
        if p.exists() and (args.check or hashlib.sha256(p.read_bytes()).hexdigest()!=previous[relative] and not args.force): failures.append(f'stale or edited: {relative}')
    if failures:
        print('\n'.join(failures[:30]),file=sys.stderr)
        return 1
    if not args.check:
        for relative,content in output.items():
            p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        for relative in stale:
            p=root/relative
            if p.exists(): p.unlink()
        manifest_path.parent.mkdir(parents=True,exist_ok=True)
        manifest_path.write_bytes(encode({p:hashlib.sha256(v).hexdigest() for p,v in sorted(output.items())}))
    print(f"{'Verified' if args.check else 'Generated'} {len(entries)} furniture items, {sum(len(e['parts']) for e in entries)} block parts, {len(output)} files; stage={args.stage}")
    return 0

if __name__=='__main__': raise SystemExit(main())
