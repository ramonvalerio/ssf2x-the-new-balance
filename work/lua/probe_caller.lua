-- Descobre quem chama a rotina compartilhada 0x2f50 lendo o endereco de retorno na
-- pilha (A7), ja que nao da pra ler o PC diretamente neste build.
local out = assert(io.open("D:/repos/SuperStreetFighter2X_Update/work/emutest/out/caller_probe.txt", "w"))

local ok_a7, a7test = pcall(memory.getregister, "a7")
out:write("getregister a7: ok=" .. tostring(ok_a7) .. " val=" .. tostring(a7test) .. "\n")
local ok_sp, sptest = pcall(memory.getregister, "sp")
out:write("getregister sp: ok=" .. tostring(ok_sp) .. " val=" .. tostring(sptest) .. "\n")
local ok_a6, a6test = pcall(memory.getregister, "a6")
out:write("getregister a6: ok=" .. tostring(ok_a6) .. " val=" .. tostring(a6test) .. "\n")
out:flush()

local callers = {}
local function hook()
  local ok, sp = pcall(memory.getregister, "a7")
  if not ok or not sp then
    ok, sp = pcall(memory.getregister, "sp")
  end
  if ok and sp then
    local ok2, ret = pcall(memory.readdword, sp)
    if ok2 and ret then
      callers[ret] = (callers[ret] or 0) + 1
    end
  end
end
memory.registerexec(0x2f50, hook)
memory.registerexec(0x2ee2, hook)

local n = 0
while n < 1800 do
  n = n + 1
  emu.frameadvance()
end

local list = {}
for addr, cnt in pairs(callers) do list[#list+1] = {addr, cnt} end
table.sort(list, function(a, b) return a[2] > b[2] end)
out:write("callers (" .. #list .. " unicos):\n")
for i = 1, math.min(#list, 60) do
  out:write(string.format("%x hits=%d\n", list[i][1], list[i][2]))
end
out:close()
local fh = io.open("D:/repos/SuperStreetFighter2X_Update/work/emutest/out/done.txt", "w")
fh:write("ok"); fh:close()
