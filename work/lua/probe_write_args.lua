local out = assert(io.open("D:/repos/SuperStreetFighter2X_Update/work/emutest/out/write_args.txt", "w"))
memory.registerwrite(0xFF844E + 0x3E, function(...)
  local n = select('#', ...)
  local parts = {}
  for i = 1, n do parts[#parts+1] = tostring(select(i, ...)) end
  out:write(emu.framecount() .. " | n=" .. n .. " | " .. table.concat(parts, ",") .. " | readword=" .. memory.readwordsigned(0xFF844E+0x3E) .. "\n")
  out:flush()
end)
local n = 0
while n < 1800 do n = n + 1; emu.frameadvance() end
out:close()
local fh = io.open("D:/repos/SuperStreetFighter2X_Update/work/emutest/out/done.txt", "w")
fh:write("ok"); fh:close()
