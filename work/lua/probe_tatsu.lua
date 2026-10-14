-- Descobre o PC exato que escreve em $88 (P1) durante o motion test do tatsu aereo instantaneo.
local ROOT = "D:/repos/SuperStreetFighter2X_Update/work/emutest/"
local OUT = ROOT .. "out/"
local log = assert(io.open(OUT .. "pc_log.csv", "w"))
log:write("frame,pc,val,p1y,p1st3\n")

memory.registerwrite(0xFF84D6, function(addr, size)
  local ok, pc = pcall(memory.getregister, "pc")
  if not ok then pc = -1 end
  local ok2, v = pcall(memory.readbyte, 0xFF84D6)
  if not ok2 then v = -1 end
  local line = tostring(emu.framecount()) .. "," .. tostring(pc) .. "," .. tostring(v) .. "\n"
  log:write(line)
  log:flush()
end)

local plan = {}
local f = io.open(ROOT .. "plan.txt", "r")
if f then
  for line in f:lines() do
    local fr, act, rest = line:match("^(%d+)%s+(%S+)%s*(.*)$")
    if fr then plan[#plan + 1] = { frame = tonumber(fr), act = act, rest = rest, done = false } end
  end
  f:close()
end

local holds = {}
local start = emu.framecount()
while true do
  local now = emu.framecount() - start
  for _, p in ipairs(plan) do
    if not p.done and now >= p.frame then
      p.done = true
      if p.act == "hold" then
        local btn, dur = p.rest:match("^(.-)%s+(%d+)$")
        holds[btn] = now + tonumber(dur)
      elseif p.act == "end" then
        log:close()
        local fh = io.open(OUT .. "done.txt", "w"); fh:write("ok " .. now); fh:close()
      end
    end
  end
  local joy = {}
  for btn, untilf in pairs(holds) do
    if now < untilf then joy[btn] = true end
  end
  joypad.set(joy)
  gui.text(4, 4, "PROBE " .. now)
  emu.frameadvance()
end
