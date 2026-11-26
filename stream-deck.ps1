# JKS Interactive: Windows PowerShell 5.1 / PowerShell 7 command launcher.
# Run with -Configure once. Credentials are DPAPI-protected for this Windows user.
[CmdletBinding()]
param([switch]$Configure,[ValidateSet('Next','Previous','Blackout','Restore','Start','Close','Pause','Resume')][string]$Action='Next')
$ErrorActionPreference='Stop'
$dir=Join-Path $env:LOCALAPPDATA 'JKS-Interactive'
$cfg=Join-Path $dir 'stream-deck.xml'
if($Configure){
    $url=(Read-Host 'HTTPS live control URL, including ?p= if applicable').Trim()
    $uri=[Uri]$url
    if($uri.Scheme -ne 'https' -or $uri.AbsolutePath -ne '/control' -or $uri.UserInfo){throw 'Enter a valid HTTPS /control URL.'}
    $secret=Read-Host 'Administrator password' -AsSecureString
    New-Item -Path $dir -ItemType Directory -Force | Out-Null
    [pscustomobject]@{Url=$url;Secret=$secret} | Export-Clixml -Path $cfg
    Write-Host 'Saved for this Windows user.'
    exit
}
if(!(Test-Path $cfg)){throw 'Run with -Configure first.'}
$c=Import-Clixml $cfg
$uri=[Uri]$c.Url
if($uri.Scheme -ne 'https' -or $uri.AbsolutePath -ne '/control' -or $uri.UserInfo){throw 'Invalid saved control URL.'}
$base=$uri.GetLeftPart([System.UriPartial]::Authority)
$bstr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($c.Secret)
try{$token=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)}finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)}
$headers=@{Authorization="Bearer $token"}
try {
    $state=Invoke-RestMethod -Method Get -Uri ($base+'/api/state'+$uri.Query) -Headers $headers -TimeoutSec 15
    $busy=($state.timerEnd -gt 0 -or $state.pausedRemaining -gt 0 -or $state.open -or $state.interaction.open)
    $body=@{}
    switch($Action){
        {$_ -in 'Next','Previous'} {
            if($busy){throw 'An interaction is active. Use the browser controller to confirm changing screens.'}
            $step=if($Action -eq 'Next'){1}else{-1}
            $index=[Math]::Max(0,[Math]::Min($state.slides.Count-1,[int]$state.screens[0]+$step))
            $body=@{screens=@($index,$index);expectedScreens=@($state.screens)}
        }
        'Blackout' {$body=@{blackout=$true}}
        'Restore' {$body=@{blackout=$false}}
        'Start' {
            if($busy){throw 'An interaction is active.'}
            $next=$state.rounds | Where-Object {$state.completed -notcontains $_.id} | Select-Object -First 1
            $hostId=$state.ledgerSlide
            if(!$next -or !$hostId){throw 'No next group available. Display a competition slide first.'}
            $body=@{guided='start';round=$next.id;slide=$hostId;epoch=$state.voteEpoch}
        }
        default {
            if(!$state.active -or !$state.competitionSlide){throw 'No current round.'}
            $body=@{guided=$Action.ToLowerInvariant();round=$state.active;slide=$state.competitionSlide;epoch=$state.voteEpoch}
        }
    }
    Invoke-RestMethod -Method Post -Uri ($base+'/api/control'+$uri.Query) -Headers $headers -ContentType 'application/json' -Body ($body|ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 15 | Out-Null
    Write-Host "$Action accepted."
} finally {$token=$null;$headers=$null}
