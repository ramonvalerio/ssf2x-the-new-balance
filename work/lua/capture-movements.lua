-- Captura frame a frame de estados, caixas e projéteis de P1/P2.
-- FBNeo: Game > Lua Scripting > New Lua Script Window > Browse > este arquivo > Run.
-- Cada execução grava um arquivo novo: work/logs/movements-AAAAMMDD-HHMMSS.csv

local out_path = "D:/repos/SuperStreetFighter2X_Update/work/logs/movements-" .. os.date("%Y%m%d-%H%M%S") .. ".csv"
os.execute('mkdir "D:\\repos\\SuperStreetFighter2X_Update\\work\\logs" 2>nul')
local f = assert(io.open(out_path, "w"))

local rb, rw, rd = memory.readbyte, memory.readword, memory.readdword
local bases = {0xFF844E, 0xFF884E}
local proj_slots = {0xFF8622, 0xFF86FC, 0xFF8A22, 0xFF8AFC}

local function attack_box(obj)
  local anim = rd(obj + 0x1A)
  if anim < 0x100 or anim > 0x400000 then return 0, 0 end
  local id = rb(anim + 0x0C)
  if id == 0 then return 0, 0 end
  local hb = rd(obj + 0x34)
  if hb < 0x100 or hb > 0x400000 then return id, -1 end
  local tbl = hb + memory.readwordsigned(hb + 6)
  return id, rb(tbl + id * 16 + 0x0B)
end

local cols = {"frame", "hitcount"}
local pf = {"char","old","x","st3","st4","st5","mv88","r55","jug2ac","inv1b3","inv1a1","inv1bf","stop47","hp2a","y","atk18b","cancel2b0","v8","v9","va","atkid","atktype","buf3f0"}
for p = 1, 2 do for _, n in ipairs(pf) do cols[#cols + 1] = "p" .. p .. "_" .. n end end
for i = 1, 4 do for _, n in ipairs({"on","atkid","atktype","y"}) do cols[#cols + 1] = "proj" .. i .. "_" .. n end end
f:write(table.concat(cols, ",") .. "\n")

local n = 0
while true do
  local row = {emu.framecount(), rb(0xFF8DE3)}
  for p = 1, 2 do
    local b = bases[p]
    local anim = rd(b + 0x1A)
    local v8, v9, va = 0, 0, 0
    if anim > 0x100 and anim < 0x400000 then v8, v9, va = rb(anim + 8), rb(anim + 9), rb(anim + 10) end
    local id, typ = attack_box(b)
    for _, v in ipairs({rb(b+0x391), rb(b+0x3B6), memory.readwordsigned(b+0x06), rb(b+3), rb(b+4), rb(b+5), rb(b+0x88), rb(b+0x55), rb(b+0x2AC), rb(b+0x1B3), rb(b+0x1A1), rb(b+0x1BF),
                        rb(b+0x47), memory.readwordsigned(b+0x2A), memory.readwordsigned(b+0x0A), rb(b+0x18B), rb(b+0x2B0), v8, v9, va, id, typ, rb(b+0x3F0)}) do
      row[#row + 1] = v
    end
  end
  for i = 1, 4 do
    local w = rw(proj_slots[i])
    if w ~= 0 then
      local obj = 0xFF0000 + w
      local id, typ = attack_box(obj)
      for _, v in ipairs({rb(obj), id, typ, memory.readwordsigned(obj + 0x0A)}) do row[#row + 1] = v end
    else
      for _ = 1, 4 do row[#row + 1] = "" end
    end
  end
  f:write(table.concat(row, ",") .. "\n")
  n = n + 1
  if n % 60 == 0 then f:flush() end
  gui.text(4, 4, "CAPTURA ATIVA (" .. n .. " frames)")
  emu.frameadvance()
end
