# Abre o emulador ISOLADO (work/emutest), carrega work/lua/auto.lua e espera work/emutest/out/done.txt.
# Não usa foco do Windows: tudo por mensagens de janela. Só mexe no processo que ele mesmo abre.
param([int]$TimeoutSec = 120, [string]$Script = 'work\lua\auto.lua')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$dir = Join-Path $root 'work\emutest'
New-Item -ItemType Directory -Force (Join-Path $dir 'out') | Out-Null
Remove-Item (Join-Path $dir 'out\done.txt') -ErrorAction SilentlyContinue
Add-Type @"
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public class A {
 public delegate bool CB(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(CB cb, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr p, CB cb, IntPtr l);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr FindWindowEx(IntPtr p, IntPtr a, string cls, string txt);
 [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, string l);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
 public static List<string> Tops(uint pid){ var r=new List<string>(); EnumWindows((h,l)=>{ uint p; GetWindowThreadProcessId(h,out p); if(p==pid){ var s=new StringBuilder(256); GetWindowText(h,s,256); var c=new StringBuilder(128); GetClassName(h,c,128); r.Add(h.ToInt64()+"|"+c+"|"+s); } return true;}, IntPtr.Zero); return r; }
 public static IntPtr Child(IntPtr top, int id){ IntPtr found=IntPtr.Zero; EnumChildWindows(top,(h,l)=>{ if(GetDlgCtrlID(h)==id){ found=h; return false;} return true;}, IntPtr.Zero); return found; }
}
"@
$p = Start-Process -FilePath (Join-Path $dir 'fcadefbneo.exe') -ArgumentList 'ssf2xjr1' -WorkingDirectory $dir -PassThru
try {
  Start-Sleep -Seconds 5
  $w = [A]::Tops($p.Id)
  $dlg = $w | Where-Object { $_ -like '*Warning*' } | Select-Object -First 1
  if ($dlg) { $hd = [IntPtr][int64]($dlg.Split('|')[0]); $b = [A]::FindWindowEx($hd, [IntPtr]::Zero, 'Button', 'OK'); [void][A]::SendMessage($b, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero) }
  $main = [IntPtr]::Zero
  for ($i = 0; $i -lt 30 -and $main -eq [IntPtr]::Zero; $i++) {
    Start-Sleep -Seconds 1
    $dlg = [A]::Tops($p.Id) | Where-Object { $_ -like '*Warning*' } | Select-Object -First 1
    if ($dlg) { $hd = [IntPtr][int64]($dlg.Split('|')[0]); $b = [A]::FindWindowEx($hd, [IntPtr]::Zero, 'Button', 'OK'); [void][A]::SendMessage($b, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero) }
    $p.Refresh(); $main = $p.MainWindowHandle
  }
  if ($main -eq [IntPtr]::Zero) { throw 'janela principal nao encontrada' }
  [void][A]::PostMessage($main, 0x0111, [IntPtr]11812, [IntPtr]::Zero)     # Game > Lua Scripting > New Lua Script Window
  Start-Sleep -Seconds 2
  $lua = [A]::Tops($p.Id) | Where-Object { $_ -like '*|Lua Script' } | Select-Object -First 1
  if (-not $lua) { throw 'janela Lua nao abriu' }
  $ld = [IntPtr][int64]($lua.Split('|')[0])
  $edit = [A]::Child($ld, 20368); $run = [A]::Child($ld, 20366)
  [void][A]::SendMessage($edit, 0x000C, [IntPtr]::Zero, (Join-Path $root $Script))
  Start-Sleep -Milliseconds 400
  [void][A]::PostMessage($ld, 0x0111, [IntPtr]20366, $run)                 # Run
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while (-not (Test-Path (Join-Path $dir 'out\done.txt'))) {
    if ((Get-Date) -gt $deadline) { throw 'tempo esgotado sem done.txt' }
    if ($p.HasExited) { throw 'emulador encerrou' }
    Start-Sleep -Milliseconds 500
  }
  'ok: ' + (Get-Content (Join-Path $dir 'out\done.txt'))
} finally {
  if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
}
