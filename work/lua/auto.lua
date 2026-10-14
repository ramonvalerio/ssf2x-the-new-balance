-- Automação sem foco para o emulador isolado (work/emutest).
-- Lê work/emutest/plan.txt (uma ação por linha) e executa em frames relativos ao início do script:
--   <frame> hold <botão> <duração>     ex.: 600 hold P1 Coin 6
--   <frame> shot <nome>                grava work/emutest/out/<nome>.gd (captura GD do jogo)
--   <frame> dump <nome>                grava obj/vram/wram de memória em work/emutest/out/<nome>-*.bin
--   <frame> end                        grava work/emutest/out/done.txt
local ROOT = "D:/repos/SuperStreetFighter2X_Update/work/emutest/"
local OUT = ROOT .. "out/"

local plan = {}
local f = io.open(ROOT .. "plan.txt", "r")
if f then
  for line in f:lines() do
    local fr, act, rest = line:match("^(%d+)%s+(%S+)%s*(.*)$")
    if fr then plan[#plan + 1] = { frame = tonumber(fr), act = act, rest = rest, done = false } end
  end
  f:close()
end

local function dumpmem(name, addr, size)
  local fh = assert(io.open(OUT .. name, "wb"))
  local parts = {}
  for a = addr, addr + size - 2, 2 do
    local w = memory.readword(a)
    parts[#parts + 1] = string.char(math.floor(w / 256) % 256, w % 256)
    if #parts >= 4096 then fh:write(table.concat(parts)); parts = {} end
  end
  fh:write(table.concat(parts)); fh:close()
end

-- Registro continuo (opcional): se work/emutest/plan.txt tiver uma linha "<frame> logstart",
-- grava work/emutest/out/log.csv a partir desse frame ate o "end".
local logfh = nil
local function log_row(now)
  if not logfh then return end
  local b1, b2 = 0xFF844E, 0xFF884E
  logfh:write(string.format("%d,%d,%d,%d,%d,%d,%d,%d\n",
    now,
    memory.readwordsigned(b1 + 0x06), memory.readwordsigned(b1 + 0x0A), memory.readbyte(b1 + 3), memory.readbyte(b1 + 0x88),
    memory.readwordsigned(b2 + 0x06), memory.readwordsigned(b2 + 0x0A), memory.readbyte(b2 + 3)))
end

local holds = {}   -- botão -> frame de término
local start = emu.framecount()
while true do
  local now = emu.framecount() - start
  for _, p in ipairs(plan) do
    if not p.done and now >= p.frame then
      p.done = true
      if p.act == "hold" then
        local btn, dur = p.rest:match("^(.-)%s+(%d+)$")
        holds[btn] = now + tonumber(dur)
      elseif p.act == "shot" then
        local g = gui.gdscreenshot()
        local fh = assert(io.open(OUT .. p.rest .. ".gd", "wb")); fh:write(g); fh:close()
      elseif p.act == "dump" then
        dumpmem(p.rest .. "-obj.bin", 0x708000, 0x2000)
        dumpmem(p.rest .. "-vram.bin", 0x900000, 0x30000)
        dumpmem(p.rest .. "-wram.bin", 0xff0000, 0x10000)
      elseif p.act == "logstart" then
        logfh = assert(io.open(OUT .. "log.csv", "w"))
        logfh:write("frame,p1_x,p1_y,p1_st3,p1_mv88,p2_x,p2_y,p2_st3\n")
      elseif p.act == "end" then
        if logfh then logfh:close(); logfh = nil end
        local fh = io.open(OUT .. "done.txt", "w"); fh:write("ok " .. now); fh:close()
      end
    end
  end
  local joy = {}
  for btn, untilf in pairs(holds) do
    if now < untilf then joy[btn] = true end
  end
  joypad.set(joy)
  log_row(now)
  gui.text(4, 4, "AUTO " .. now)
  emu.frameadvance()
end
