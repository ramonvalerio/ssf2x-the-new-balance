-- Testa se memory.registerexec realmente dispara neste build, usando um endereco que
-- sabemos que executa (o hook do fix da bola do Blanka, 0x80f60, chamado toda vez que
-- o jogo decide a reacao do golpe tipo 0x14 -- nao precisa ser a bola do Blanka
-- especificamente, mas ajuda se vc acertar ela pra confirmar rapido).
local out_path = "D:/repos/SuperStreetFighter2X_Update/work/logs/exec-sanity.csv"
local f = assert(io.open(out_path, "w"))
f:write("frame,hits\n")
local hits = 0
memory.registerexec(0x80f60, function() hits = hits + 1 end)

local n = 0
while true do
  n = n + 1
  if n % 30 == 0 then f:write(n .. "," .. hits .. "\n"); f:flush() end
  gui.text(4, 4, "SANITY " .. n .. " hits=" .. hits)
  emu.frameadvance()
end
