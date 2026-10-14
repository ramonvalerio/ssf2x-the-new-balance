from pathlib import Path
import zipfile,hashlib,json,copy
root=Path('docs/specs/characters/fei-long/new/0001-chicken-wing-meia-lua.md'); root.mkdir(parents=True,exist_ok=True)
a=zipfile.ZipFile('ssf2xjr1.zip'); b=zipfile.ZipFile('chicken-wing-test.zip')
old=a.read('sfxj.04a'); new=b.read('sfxj.04a')
diff=[i for i,(x,y) in enumerate(zip(old,new)) if x!=y]
assert diff==[0x151d6,0x151d7],diff
with zipfile.ZipFile(root/'ssf2xjr1.zip','w',zipfile.ZIP_DEFLATED) as out:
 for item in a.infolist(): out.writestr(copy.copy(item),new if item.filename=='sfxj.04a' else a.read(item.filename))
p=diff[0]; patch=b'PATCH'+p.to_bytes(3,'big')+(2).to_bytes(2,'big')+new[p:p+2]+b'EOF'
(root/'sfxj.04a.ips').write_bytes(patch)
report={'source_sha256':hashlib.sha256(Path('ssf2xjr1.zip').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((root/'ssf2xjr1.zip').read_bytes()).hexdigest(),'rom_file':'sfxj.04a','file_offset':hex(p),'encrypted_before':old[p:p+2].hex(),'encrypted_after':new[p:p+2].hex(),'cpu_instruction_address':'0x0951d4','original_instruction':'cmpi.w #$000a,d0','modified_instruction':'cmpi.w #$0002,d0','tests':json.loads(Path('work/command-tests.json').read_text())}
(root/'verification.json').write_text(json.dumps(report,indent=2))
with zipfile.ZipFile(root/'ssf2xjr1.zip') as out:
 assert out.testzip() is None
 assert out.namelist()==a.namelist()
 assert [n for n in a.namelist() if a.read(n)!=out.read(n)]==['sfxj.04a']
print(json.dumps(report,indent=2))
