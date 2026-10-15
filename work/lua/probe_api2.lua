local out = assert(io.open("D:/repos/SuperStreetFighter2X_Update/work/emutest/out/api_probe2.txt", "w"))
out:write("-- globals --\n")
for k, v in pairs(_G) do out:write(tostring(k) .. " = " .. type(v) .. "\n") end

out:write("-- registerexec callback args --\n")
local got = {}
memory.registerexec(0x81c18, function(...)
  local n = select('#', ...)
  got[#got+1] = n .. ":" .. table.concat({...}, ",")
end)

local n = 0
while n < 300 do
  n = n + 1
  emu.frameadvance()
end
out:write("calls: " .. #got .. "\n")
for i = 1, math.min(#got, 5) do out:write(got[i] .. "\n") end
out:close()
local fh = io.open("D:/repos/SuperStreetFighter2X_Update/work/emutest/out/done.txt", "w")
fh:write("ok"); fh:close()
