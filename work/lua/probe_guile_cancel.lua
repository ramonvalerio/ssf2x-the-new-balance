-- Combina contagem de execucao com os campos de memoria relevantes, tudo no mesmo
-- quadro, pra correlacionar sem ambiguidade.
local out_path = "D:/repos/SuperStreetFighter2X_Update/work/logs/guile-cancel-combined.csv"
local f = assert(io.open(out_path, "w"))

local b1 = 0xFF844E
local candidates = {0x7f018, 0x7b38e, 0x84340, 0x84354, 0x8437c, 0x84390, 0x843b8, 0x8439e, 0x84960, 0x849c2}
local counts = {}
for _, a in ipairs(candidates) do
  counts[a] = 0
  memory.registerexec(a, function() counts[a] = counts[a] + 1 end)
end

local header = {"frame", "atkid", "spc195", "cancel2b0", "st3"}
for _, a in ipairs(candidates) do header[#header + 1] = string.format("hit%x", a) end
f:write(table.concat(header, ",") .. "\n")

local function attack_box(obj)
  local anim = memory.readdword(obj + 0x1A)
  if anim < 0x100 or anim > 0x400000 then return 0 end
  return memory.readbyte(anim + 0x0C)
end

local n = 0
while true do
  n = n + 1
  local id = attack_box(b1)
  local row = {n, id, memory.readbyte(b1 + 0x195), memory.readbyte(b1 + 0x2B0), memory.readbyte(b1 + 3)}
  for _, a in ipairs(candidates) do row[#row + 1] = counts[a] end
  f:write(table.concat(row, ",") .. "\n")
  if n % 10 == 0 then f:flush() end
  gui.text(4, 4, "GUILE COMBINED (" .. n .. ")")
  emu.frameadvance()
end
